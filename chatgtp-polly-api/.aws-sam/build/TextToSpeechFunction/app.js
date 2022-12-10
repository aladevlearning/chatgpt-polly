const { StartSpeechSynthesisTaskCommand  } = require("@aws-sdk/client-polly");
const { PollyClient } =require( "@aws-sdk/client-polly");


const pollyClient = new PollyClient({ region: process.env.REGION });


exports.lambdaHandler = async (event, context) => {

    const body = JSON.parse(event.body);

    var params = {
      OutputFormat: "mp3",
      OutputS3BucketName: process.env.OUTPUT_S3_BUCKET,
      Text: body.Answer,
      TextType: "text",
      VoiceId: "Joanna",
      SampleRate: "22050",
    };

    try {
        const f = await pollyClient.send(new StartSpeechSynthesisTaskCommand(params));
        console.log("Success, audio file added to " + params.OutputS3BucketName, f);

        return {
                statusCode: 200,
                body:JSON.stringify("Success"),
                }

      } catch (err) {
        console.log("Error putting object", err);
        return {
                statusCode: 500,
                body:JSON.stringify("Error putting object"),
        }
      }



};
