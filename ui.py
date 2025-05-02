import chainlit as cl
import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerSse
from agents.model_settings import ModelSettings
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize the MCP server
server = None
agent = None

# Store chat history
chat_history = []

async def setup_agent():
    """Initialize the MCP server and agent"""
    global server, agent
    
    server = MCPServerSse(
        name="Prokerala SSE Server",
        params={
            "url": "http://localhost:8000/sse",
        },
    )
    await server.connect()

    print("Server Connected")
    
    agent = Agent(
        name="Prokerala Assistant",
        instructions="Use the Prokerala API tools to answer questions about astrology, horoscopes, and panchang. For datetime inputs, use the format: YYYY-MM-DD HH:MM AM/PM",
        mcp_servers=[server],
        model_settings=ModelSettings(tool_choice="auto"),
    )
    print("Agent Created")

    chat_history.append({"role": "system", "content": "Todays date is"+ datetime.now().strftime("%Y-%m-%d")})

@cl.on_chat_start
async def start():
    """Initialize the chat session"""
    await setup_agent()
    await cl.Message(
        content="Welcome to Prokerala Astrology Assistant! How can I help you today?",
        author="System"
    ).send()

@cl.on_message
async def main(message: cl.Message):

    global agent
    """Handle incoming messages"""
    try:
        # # Add user message to chat history
        chat_history.append({"role": "user", "content": message.content})
        
        # Run the agent with the message directly
        result = await Runner.run(
            starting_agent=agent,
            input=chat_history
        )

        # print(result.final_output)
        
        # # Add assistant response to chat history
        # chat_history.append({"role": "assistant", "content": result.final_output})
        
        await cl.Message(
            content=result.final_output,
            author="User"
        ).send()
        
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        await cl.Message(
            content=error_msg,
            author="Error"
        ).send()
        chat_history.append({"role": "assistant", "content": error_msg})

@cl.on_chat_end
async def end():
    """Clean up when chat ends"""
    if server:
        await server.cleanup()
    chat_history.clear()
