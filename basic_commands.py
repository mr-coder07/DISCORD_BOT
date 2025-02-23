import discord
from discord.ext import commands
import datetime
import asyncio
from collections import defaultdict
import json
import os
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class CompetitionConfig:
    def __init__(self):
        self.POINTS_PER_QUESTION = 5
        self.TIME_LIMIT_MINUTES = 1
        self.TOTAL_QUESTIONS = 3
        self.POINT_LOSS_PER_MINUTE = 1
        self.SAVE_FILE = "competition_data.json"
        self.QUESTIONS = {
            1: {"question": "What is the capital of France?", "answer": "Paris"},
            2: {"question": "What is 2 + 2?", "answer": "4"},
            3: {"question": "Who wrote 'Romeo and Juliet'?", "answer": "Shakespeare"}
        }
        self.QUESTION_TIMEOUT = 300  # 5 minutes in seconds

class Competition(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = CompetitionConfig()
        self.active_competitions = {}
        self.leaderboard = defaultdict(int)
        self.question_timestamps = {}
        self.participant_channels = {}  # Maps user IDs to competition channels
        self.load_data()

    def load_data(self):
        """Load saved leaderboard data"""
        try:
            if os.path.exists(self.config.SAVE_FILE):
                with open(self.config.SAVE_FILE, 'r') as f:
                    data = json.load(f)
                    self.leaderboard = defaultdict(int, data.get('leaderboard', {}))
                logger.info("Leaderboard data loaded successfully")
        except Exception as e:
            logger.error(f"Error loading data: {e}")

    @commands.command(name='startcomp')
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def start_competition(self, ctx):
        """Start a new competition"""
        try:
            if ctx.channel in self.active_competitions:
                await ctx.send("❌ A competition is already running in this channel!")
                return

            # Lock down the channel
            await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
            
            self.active_competitions[ctx.channel] = {
                "start_time": datetime.datetime.now(),
                "is_active": True,
                "current_question": 1,
                "participants": {}
            }

            # Send introduction message
            intro_embed = discord.Embed(
                title="🎮 New Competition Started!",
                description=(
                    "**How to participate:**\n"
                    "1. Questions will appear in this channel\n"
                    "2. Send your answers in DM to the bot\n"
                    "3. Use the format: `!answer <question_number> <your_answer>`\n"
                    "4. Results will be posted here, but answers stay private\n\n"
                    "Good luck! 🍀"
                ),
                color=discord.Color.green()
            )
            await ctx.send(embed=intro_embed)

            # Store the competition channel for each participant
            for member in ctx.channel.members:
                if not member.bot:
                    self.participant_channels[member.id] = ctx.channel
                    try:
                        welcome_dm = discord.Embed(
                            title="🎯 Competition Instructions",
                            description=(
                                "A competition has started!\n\n"
                                "- Send your answers here in DM\n"
                                "- Use: `!answer <question_number> <your_answer>`\n"
                                "- Example: `!answer 1 Paris`\n\n"
                                "Good luck! 🌟"
                            ),
                            color=discord.Color.blue()
                        )
                        await member.send(embed=welcome_dm)
                    except discord.Forbidden:
                        await ctx.send(f"⚠️ Couldn't send DM to {member.mention}. Please enable DMs to participate!")

            await self.ask_next_question(ctx.channel)

        except Exception as e:
            logger.error(f"Error starting competition: {e}")
            await ctx.send("❌ Error starting competition. Please try again.")
            # Cleanup if needed
            if ctx.channel in self.active_competitions:
                del self.active_competitions[ctx.channel]
                await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)

    @commands.command(name='answer')
    @commands.dm_only()
    async def submit_answer(self, ctx, question_number: int, *, answer: str):
        """Submit an answer via DM"""
        try:
            # Check if user is participating in any competition
            if ctx.author.id not in self.participant_channels:
                await ctx.send("❌ You're not currently participating in any competition!")
                return

            competition_channel = self.participant_channels[ctx.author.id]
            comp = self.active_competitions.get(competition_channel)

            if not comp or not comp['is_active']:
                await ctx.send("❌ No active competition found!")
                return

            if not 1 <= question_number <= self.config.TOTAL_QUESTIONS:
                await ctx.send(f"❌ Question number must be between 1 and {self.config.TOTAL_QUESTIONS}")
                return

            if question_number != comp['current_question']:
                await ctx.send(f"❌ This is not the current question. Please answer question {comp['current_question']}.")
                return

            # Process answer
            correct_answer = self.config.QUESTIONS[question_number]['answer'].lower()
            if answer.lower().strip() != correct_answer:
                await ctx.send("❌ Incorrect answer. Try again!")
                return

            # Calculate points
            time_taken = datetime.datetime.now() - self.question_timestamps[question_number]
            minutes_taken = time_taken.total_seconds() / 60
            points = self.config.POINTS_PER_QUESTION
            points_lost = min(int(minutes_taken) * self.config.POINT_LOSS_PER_MINUTE, points)
            final_points = max(0, points - points_lost)

            # Update leaderboard
            self.leaderboard[ctx.author.name] += final_points

            # Send private success message
            success_embed = discord.Embed(
                title="✅ Correct Answer!",
                color=discord.Color.green()
            )
            success_embed.add_field(name="Points Earned", value=str(final_points))
            success_embed.add_field(name="Time Taken", value=f"{minutes_taken:.1f} minutes")
            await ctx.send(embed=success_embed)

            # Update competition channel
            await competition_channel.send(f"🎉 {ctx.author.mention} answered correctly!")
            await self.show_leaderboard(competition_channel)

            # Move to next question
            comp['current_question'] += 1
            await self.ask_next_question(competition_channel)

        except Exception as e:
            logger.error(f"Error processing answer: {e}")
            await ctx.send("❌ An error occurred while processing your answer.")

    async def ask_next_question(self, channel):
        """Ask the next question in the competition"""
        if channel not in self.active_competitions:
            return

        comp = self.active_competitions[channel]
        current_question = comp['current_question']

        if current_question > self.config.TOTAL_QUESTIONS:
            await self.end_competition(channel)
            return

        question = self.config.QUESTIONS[current_question]['question']
        embed = discord.Embed(
            title=f"❓ Question {current_question}",
            description=question,
            color=discord.Color.blue()
        )
        embed.set_footer(text="Send your answer in DM to the bot using !answer")
        
        await channel.send(embed=embed)
        self.question_timestamps[current_question] = datetime.datetime.now()

        # Set up question timeout
        await asyncio.sleep(self.config.QUESTION_TIMEOUT)
        if channel in self.active_competitions and comp['current_question'] == current_question:
            await channel.send(f"⏰ Time's up for question {current_question}!")
            comp['current_question'] += 1
            await self.ask_next_question(channel)

    @commands.command(name='endcomp')
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def end_competition(self, ctx):
        """End the current competition"""
        channel = ctx if isinstance(ctx, discord.TextChannel) else ctx.channel
        
        if channel not in self.active_competitions:
            if not isinstance(ctx, discord.TextChannel):
                await ctx.send("❌ No active competition to end!")
            return

        # Show final results
        await self.show_leaderboard(channel)
        
        # Clean up
        del self.active_competitions[channel]
        
        # Remove participants from tracking
        self.participant_channels = {k: v for k, v in self.participant_channels.items() if v != channel}
        
        # Unlock the channel
        await channel.set_permissions(channel.guild.default_role, send_messages=None)
        
        await channel.send(embed=discord.Embed(
            title="🎉 Competition Ended!",
            description="Thanks for participating!",
            color=discord.Color.green()
        ))

    @commands.Cog.listener()
    async def on_message(self, message):
        """Prevent answer attempts in public channels"""
        if message.author.bot or isinstance(message.channel, discord.DMChannel):
            return

        if message.channel in self.active_competitions:
            if message.content.lower().startswith('!answer'):
                try:
                    await message.delete()
                    reminder = await message.channel.send(
                        f"{message.author.mention} Please send your answers in DM to the bot!",
                        delete_after=5
                    )
                except discord.Forbidden:
                    pass

    @commands.command(name='lb')
    #async def show_leaderboard(self, ctx):
    #    """Display the current leaderboard"""
    #    if ctx.channel in self.active_competitions:
    #        await self.show_leaderboard(ctx.channel)
    #    else:
    #        await ctx.send("❌ There is no active competition to display a leaderboard for.")

    async def show_leaderboard(self, channel: discord.TextChannel):
        """Show the current leaderboard in the competition channel"""
        if self.leaderboard:
            embed = discord.Embed(
                title="🏆 Leaderboard",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.now()
            )
            for position, (name, score) in enumerate(sorted(self.leaderboard.items(), key=lambda x: x[1], reverse=True),
                                                     start=1):
                embed.add_field(name=f"{position}. {name}", value=f"Score: {score}", inline=False)
            await channel.send(embed=embed)
        else:
            await channel.send("📊 No scores recorded for this competition!")

def setup(bot):
    bot.add_cog(Competition(bot))
