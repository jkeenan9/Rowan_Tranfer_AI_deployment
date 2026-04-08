# Rowan_Transfer_Advisor
Building an AI tool to help Rowan transfer students 

If this project turns into a clinic project, or placed in the hands of others, and you are reading this, feel free to contact me at jameskeenan708@gmail.com I would be more than happy to explain my messy creation!

IMPORTANT:
As of 04/08/26 I have removed the OpenAI API token, and the website will not respond correctly. Please follow Streamlits procedure on how to replace an API secret.

Future Works:
1) Improvement of initializing schedule building functionality. As of 04/08/26 the schedule building function activates only when the user asks "make me a schedule. I have taken [exact me course 1], [exact me course 2]," ... This is not robust. A better approach may be creating an entirely new page with a seperate AI chat point that only deals with schedule building.

2) Update the chatbots sources. This chatbot is a file search tool that is only as good as the information it has access to. The last update to the knowledge base was 12/2026.

3) Authorization functionality. Adding this would allow a creation of a database storing users and user history, while providing a more secure and robust login system. The userbase is crucial data that can one day be used to train a specific Rowan Engineering transfer LLM. I had been looking into integrating oAuth for this functionality, could be a good start. 
