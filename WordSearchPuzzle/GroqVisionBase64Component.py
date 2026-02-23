

from langflow.custom import Component
from langflow.inputs import StrInput, SecretStrInput, MessageTextInput, DropdownInput
from langflow.io import Output
from langflow.schema import Data, Message
from groq import Groq
import base64


class GroqVisionBase64Component(Component):
  display_name = "Groq Vision (Base64)"
  description = "Send base64 image data to Groq's multimodal models"
  documentation = "https://console.groq.com/docs/vision"
  icon = "Groq"
  
  inputs = [
      SecretStrInput(
          name="groq_api_key",
          display_name="Groq API Key",
          required=True,
          info="Your Groq API key from https://console.groq.com"
      ),
      MessageTextInput(
          name="base64_image",
          display_name="Base64 Image Data",
          required=True,
          info="Base64 encoded image data (can include data URI prefix or just the base64 string)"
      ),
      MessageTextInput(
          name="prompt",
          display_name="Text Prompt",
          required=True,
          info="Your question or instruction about the image"
      ),
      DropdownInput(
          name="model",
          display_name="Model",
          options=[
              "llama-3.2-90b-vision-preview",
              "llama-3.2-11b-vision-preview",
              "meta-llama/llama-4-maverick-17b-128e-instruct"
          ],
          value="llama-3.2-90b-vision-preview",
          info="Groq vision model to use"
      ),
      DropdownInput(
          name="image_type",
          display_name="Image Type",
          options=[
              "image/jpeg",
              "image/png",
              "image/gif",
              "image/webp"
          ],
          value="image/jpeg",
          info="MIME type of the image"
      )
  ]
  
  outputs = [
      Output(type=Message, display_name="Response", name="response", method="process_image"),
  ]
  
  def process_image(self) -> Message:
      try:
          # Initialize Groq client
          client = Groq(api_key=self.groq_api_key)
          
          # Clean the base64 data
          base64_data = self.base64_image.strip()
          
          # Remove data URI prefix if present
          if base64_data.startswith('data:'):
              base64_data = base64_data.split(',', 1)[1]
          
          # Construct the image URL for Groq API
          image_url = f"data:{self.image_type};base64,{base64_data}"
          
          # Create the messages payload
          messages = [
              {
                  "role": "user",
                  "content": [
                      {
                          "type": "text",
                          "text": self.prompt
                      },
                      {
                          "type": "image_url",
                          "image_url": {
                              "url": image_url
                          }
                      }
                  ]
              }
          ]
          
          # Call Groq API
          chat_completion = client.chat.completions.create(
              messages=messages,
              model=self.model
          )
          
          # Extract response
          response_text = chat_completion.choices[0].message.content
          
          return Message(text=response_text)
          
      except Exception as e:
          error_msg = f"Error processing image with Groq: {str(e)}"
          self.log(error_msg)
          return Data(
              data={
                  "response": error_msg,
                  "error": True
              }
          )