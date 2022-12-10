import { Configuration, OpenAIApi } from "openai";

const configuration = new Configuration({
  apiKey: process.env.OPENAI_API_KEY,
});

const openai = new OpenAIApi(configuration);

export const lambdaHandler = async (event, context) => {

    const completion = await openai.createCompletion({
        model: "text-ada-001",
        prompt: event.question,
        temperature: 0.6,
        echo: true,
        max_tokens: 2048
      });

   return {
        statusCode: 200,
        body:JSON.stringify({"Answer": completion.data.choices[0].text }),
    }
};
