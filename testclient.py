import asyncio
import os
from agents import Agent, Runner
from agents.mcp import MCPServerSse
from agents.model_settings import ModelSettings
from dotenv import load_dotenv
import json
from datetime import datetime
# Load .env
load_dotenv()

# run fastmcp run mcp-server-openai.py:mcp --transport sse
#before running this, run the mcp-server-openai.py file

async def main():
    server = MCPServerSse(
        name="Prokerala SSE Server",
        params={
            "url": "http://localhost:8000/sse",
        },
    )
    await server.connect()  # Initialize the server connection

    # tools = await server.list_tools()
    # # Print tools in a readable JSON format
    # print(json.dumps(tools, indent=2, default=lambda x: x.__dict__))

    
    agent = Agent(
        name="Prokerala Assistant",
        instructions="""You are vedic astrologer. Chat normally and get required information from the user for generatring vedic astrology report. 
        Use the Prokerala API tools to answer questions about astrology, horoscopes, and panchang. 
        Follow tool description and parameters strictly.
        People never provide latitude and longitude, so you ask for the place datails, and you use your knowledge to get the latitude and longitude.
        If you don't know the exact latitude and longitude, use the district or state to get that. (avoid country, as it is huge)
        Use the previous conversation history to generate the report.
        Call tool only when you really need, also only after proper parameters are fully received from the user.
        
        """,
        mcp_servers=[server],
        model_settings=ModelSettings(tool_choice="auto"),
    )


    history = []
    history.append({"role": "system", "content": "Todays date and time is" + datetime.now().strftime("%Y-%m-%d %H:%M:%S")})


    while True:
        
        message = input("Enter your message: ")
        if message == "exit":
            await server.cleanup()
            break

        history.append({"role": "user", "content": message})

        result = await Runner.run(starting_agent=agent, input=history)
        print(result.final_output)

        history.append({"role": "assistant", "content": result.final_output})


    await server.cleanup()  # Clean up the server connection

if __name__ == "__main__":
    asyncio.run(main())
 