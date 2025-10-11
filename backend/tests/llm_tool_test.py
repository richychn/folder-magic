import json
import asyncio
from openai import OpenAI
from backend.app.tools import propose_actions_tool
from backend.app.tool_schema import ProposeActionsInput

async def main():
    client = OpenAI()

    tools = [
        {
            "type": "function",
            "function": {
                "name": "propose_actions_tool",
                "description": "Propose and execute file/folder actions for a user.",
                "parameters": ProposeActionsInput.model_json_schema(),
            },
        }
    ]

    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that is helping the user organize their Google Drive."},
            {"role": "user", "content": "for tjiang217@gmail.com move file id 1ZHM5nX4mzoLs6a26BUcSbl6PKJ5Y4pqmC1KAYfmlz6M to folder id 1yqIplLn9keODMIjNOy1V6o0U33_2i_NW and rename folder id 1SB6uExQHRknz8wz1Ui0xOAfh_TKQ8vxIltEjzqzBgPs to test123"},
        ],
        tools=tools,
    )

    tool_call = response.choices[0].message.tool_calls[0]
    args = json.loads(tool_call.function.arguments)
    print("LLM proposed:", args)

    result = await propose_actions_tool(args)
    print("Tool result:", result)

# Run the async function
asyncio.run(main())
