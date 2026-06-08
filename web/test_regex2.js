const str = `<thought>The user wants a short name for the conversation.
The conversation history consists of:
User: "Test this ticket - CRSETRI-2076 using URL https://qa.creditmobility.net/"
Assistant: (Internal thought process and response asking for ticket details)

The main topic is testing JIRA ticket CRSETRI-2076.
Language: English.
Keywords: Test, CRSETRI-2076.</thought>Test CRSETRI-2076`;

const cleaned = str.replace(/<(?:thought|think)>[\s\S]*?(?:<\/(?:thought|think)>|$)/gi, '').trim();
console.log("Original length:", str.length);
console.log("Cleaned:", cleaned);
