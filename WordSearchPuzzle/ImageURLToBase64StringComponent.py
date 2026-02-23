# image_url_to_base64_string.py
# Upload via Langflow UI > Custom Components

import base64
import requests
from urllib.parse import urlparse

from langflow.custom import Component
from langflow.io import MessageTextInput, Output
from langflow.schema.message import Message


class ImageURLToBase64StringComponent(Component):
    """
    Custom Langflow Component
    ─────────────────────────
    Takes an image URL as input and returns
    ONLY the raw Base64 string as a Message output.
    """

    # ── Component Metadata ────────────────────────────────────────────────────
    display_name = "Image URL → Base64 String"
    description  = "Fetches an image from a URL and returns only the raw Base64 encoded string."
    icon         = "image"
    name         = "ImageURLToBase64String"

    # ── Inputs ────────────────────────────────────────────────────────────────
    inputs = [
        MessageTextInput(
            name         = "image_url",
            display_name = "Image URL",
            info         = "The HTTP/HTTPS URL of the image to convert to Base64.",
            required     = True,
            placeholder  = "https://example.com/image.jpg",
        ),
    ]

    # ── Outputs ───────────────────────────────────────────────────────────────
    outputs = [
        Output(
            display_name = "Base64 String",
            name         = "base64_string",
            method       = "convert_image",
        ),
    ]

    # ── Core Logic ────────────────────────────────────────────────────────────
    def convert_image(self) -> Message:
        """Fetch image from URL and return ONLY the Base64 string as Message."""
        try:
            image_url = self.image_url.strip()

            # ── Step 1: Validate URL ──────────────────────────────────────
            if not image_url:
                raise ValueError("Image URL cannot be empty.")

            parsed = urlparse(image_url)

            if not parsed.scheme or not parsed.netloc:
                raise ValueError(f"Invalid URL format: '{image_url}'")

            if parsed.scheme not in ("http", "https"):
                raise ValueError(
                    f"Only http/https URLs supported. Got: '{parsed.scheme}'"
                )

            # ── Step 2: Fetch Image ───────────────────────────────────────
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }

            response = requests.get(
                image_url,
                headers = headers,
                timeout = 15,
            )
            response.raise_for_status()

            # ── Step 3: Validate Image Data ───────────────────────────────
            image_data = response.content

            if not image_data:
                raise RuntimeError("Empty response — no image data received.")

            content_type = (
                response.headers.get("Content-Type", "image/jpeg")
                .split(";")[0]
                .strip()
            )

            if not content_type.startswith("image/"):
                raise ValueError(
                    f"URL does not point to an image. "
                    f"Content-Type received: '{content_type}'"
                )

            # ── Step 4: Convert to Base64 ─────────────────────────────────
            base64_string = base64.b64encode(image_data).decode("utf-8")

            self.status = (
                f"✅ Success | "
                f"Type: {content_type} | "
                f"Size: {len(image_data):,} bytes"
            )

            # ── Step 5: Return ONLY the Base64 string ─────────────────────
            return Message(text=base64_string)

        # ── Error Handling ────────────────────────────────────────────────────
        except ValueError as e:
            self.status = f"❌ Validation error: {str(e)}"
            raise Exception(f"Invalid input: {str(e)}")

        except requests.exceptions.ConnectionError:
            self.status = f"❌ Connection failed: {self.image_url}"
            raise Exception(
                f"Could not connect to: {self.image_url}. "
                "Check the URL or your internet connection."
            )

        except requests.exceptions.Timeout:
            self.status = f"❌ Timeout: {self.image_url}"
            raise Exception(
                f"Request timed out after 15s for: {self.image_url}"
            )

        except requests.exceptions.HTTPError as e:
            code = e.response.status_code if e.response else "?"
            self.status = f"❌ HTTP {code} error"
            raise Exception(f"HTTP {code} error fetching image: {str(e)}")

        except Exception as e:
            self.status = f"❌ Error: {str(e)}"
            raise Exception(f"Failed to convert image: {str(e)}")