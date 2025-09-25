"""
ماژول تولید محتوای چندرسانه‌ای
تولید عکس، صوت، موزیک، ویدیو
"""

import asyncio
import aiohttp
import openai
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import base64
import io
import json
import os
from pathlib import Path
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import requests

from config.settings import settings


class ImageGenerator:
    """تولیدکننده تصاویر"""
    
    def __init__(self):
        self.dalle_available = bool(settings.openai_api_key)
        self.stable_diffusion_available = False  # باید با API خارجی پیاده‌سازی شود
        
        if settings.openai_api_key:
            openai.api_key = settings.openai_api_key
    
    async def generate_image(
        self, 
        prompt: str, 
        style: str = "realistic",
        size: str = "1024x1024",
        quality: str = "standard"
    ) -> Dict[str, Any]:
        """تولید تصویر از متن"""
        
        try:
            # بهبود prompt بر اساس سبک
            enhanced_prompt = self._enhance_prompt(prompt, style)
            
            if self.dalle_available:
                return await self._generate_with_dalle(enhanced_prompt, size, quality)
            else:
                return await self._generate_placeholder_image(prompt, size)
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "prompt": prompt
            }
    
    def _enhance_prompt(self, prompt: str, style: str) -> str:
        """بهبود prompt بر اساس سبک"""
        
        style_modifiers = {
            "realistic": "photorealistic, high quality, detailed, professional photography",
            "artistic": "artistic, creative, beautiful composition, masterpiece",
            "cartoon": "cartoon style, animated, colorful, fun, digital art",
            "abstract": "abstract art, modern, creative, unique perspective",
            "vintage": "vintage style, retro, classic, nostalgic atmosphere",
            "minimalist": "minimalist, clean, simple, elegant design",
            "fantasy": "fantasy art, magical, mystical, enchanting, detailed"
        }
        
        modifier = style_modifiers.get(style, style_modifiers["realistic"])
        return f"{prompt}, {modifier}"
    
    async def _generate_with_dalle(
        self, 
        prompt: str, 
        size: str,
        quality: str
    ) -> Dict[str, Any]:
        """تولید با DALL-E"""
        
        try:
            response = await openai.Image.acreate(
                prompt=prompt,
                n=1,
                size=size,
                quality=quality,
                response_format="b64_json"
            )
            
            image_data = response.data[0].b64_json
            
            # ذخیره تصویر
            image_path = await self._save_image_from_base64(image_data, prompt)
            
            return {
                "success": True,
                "image_path": image_path,
                "image_data": image_data,
                "prompt": prompt,
                "size": size,
                "quality": quality,
                "generator": "dalle-3",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"DALL-E error: {str(e)}",
                "prompt": prompt
            }
    
    async def _generate_placeholder_image(
        self, 
        prompt: str, 
        size: str
    ) -> Dict[str, Any]:
        """تولید تصویر placeholder"""
        
        try:
            width, height = map(int, size.split('x'))
            
            # ایجاد تصویر ساده
            image = Image.new('RGB', (width, height), color='lightblue')
            draw = ImageDraw.Draw(image)
            
            # اضافه کردن متن
            try:
                font = ImageFont.truetype("arial.ttf", 40)
            except:
                font = ImageFont.load_default()
            
            text = f"Generated: {prompt[:50]}..."
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            draw.text((x, y), text, fill='darkblue', font=font)
            
            # ذخیره تصویر
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"placeholder_{timestamp}.png"
            filepath = Path("generated_images") / filename
            filepath.parent.mkdir(exist_ok=True)
            
            image.save(filepath)
            
            return {
                "success": True,
                "image_path": str(filepath),
                "prompt": prompt,
                "size": size,
                "generator": "placeholder",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Placeholder generation error: {str(e)}"
            }
    
    async def _save_image_from_base64(self, base64_data: str, prompt: str) -> str:
        """ذخیره تصویر از base64"""
        
        image_data = base64.b64decode(base64_data)
        image = Image.open(io.BytesIO(image_data))
        
        # ایجاد نام فایل
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_prompt = "".join(c for c in prompt[:20] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_prompt}_{timestamp}.png".replace(' ', '_')
        
        filepath = Path("generated_images") / filename
        filepath.parent.mkdir(exist_ok=True)
        
        image.save(filepath)
        return str(filepath)
    
    async def edit_image(
        self, 
        image_path: str, 
        prompt: str,
        mask_path: str = None
    ) -> Dict[str, Any]:
        """ویرایش تصویر"""
        
        try:
            if not self.dalle_available:
                return {
                    "success": False,
                    "error": "Image editing requires DALL-E API"
                }
            
            with open(image_path, 'rb') as image_file:
                if mask_path:
                    with open(mask_path, 'rb') as mask_file:
                        response = await openai.Image.acreate_edit(
                            image=image_file,
                            mask=mask_file,
                            prompt=prompt,
                            n=1,
                            size="1024x1024",
                            response_format="b64_json"
                        )
                else:
                    response = await openai.Image.acreate_variation(
                        image=image_file,
                        n=1,
                        size="1024x1024",
                        response_format="b64_json"
                    )
            
            image_data = response.data[0].b64_json
            edited_image_path = await self._save_image_from_base64(image_data, f"edited_{prompt}")
            
            return {
                "success": True,
                "original_image": image_path,
                "edited_image": edited_image_path,
                "prompt": prompt,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Image editing error: {str(e)}"
            }


class AudioGenerator:
    """تولیدکننده صوت و موزیک"""
    
    def __init__(self):
        self.tts_available = True  # از ماژول voice استفاده می‌کند
        self.music_generation_available = False  # نیاز به API خارجی
    
    async def generate_speech(
        self, 
        text: str, 
        voice: str = "alloy",
        speed: float = 1.0
    ) -> Dict[str, Any]:
        """تولید گفتار از متن"""
        
        try:
            if not settings.openai_api_key:
                return {
                    "success": False,
                    "error": "OpenAI API key required for speech generation"
                }
            
            response = await openai.Audio.acreate_speech(
                model="tts-1",
                voice=voice,
                input=text,
                speed=speed
            )
            
            # ذخیره فایل صوتی
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"speech_{timestamp}.mp3"
            filepath = Path("generated_audio") / filename
            filepath.parent.mkdir(exist_ok=True)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return {
                "success": True,
                "audio_path": str(filepath),
                "text": text,
                "voice": voice,
                "speed": speed,
                "duration_estimate": len(text) * 0.1,  # تخمین مدت زمان
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Speech generation error: {str(e)}"
            }
    
    async def generate_music(
        self, 
        prompt: str, 
        duration: int = 30,
        genre: str = "ambient"
    ) -> Dict[str, Any]:
        """تولید موزیک (شبیه‌سازی)"""
        
        # این یک شبیه‌سازی است - در پیاده‌سازی واقعی باید از API هایی مثل MusicGen استفاده کرد
        
        try:
            # ایجاد فایل موزیک ساده (placeholder)
            import wave
            import math
            
            sample_rate = 44100
            duration_samples = int(duration * sample_rate)
            
            # تولید موج ساده
            frequency = 440  # A note
            samples = []
            
            for i in range(duration_samples):
                t = i / sample_rate
                # موج سینوسی ساده با تغییرات
                amplitude = 0.3 * math.sin(2 * math.pi * frequency * t) * math.exp(-t/10)
                samples.append(int(amplitude * 32767))
            
            # ذخیره فایل WAV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"music_{timestamp}.wav"
            filepath = Path("generated_audio") / filename
            filepath.parent.mkdir(exist_ok=True)
            
            with wave.open(str(filepath), 'w') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(b''.join(sample.to_bytes(2, 'little', signed=True) for sample in samples))
            
            return {
                "success": True,
                "audio_path": str(filepath),
                "prompt": prompt,
                "duration": duration,
                "genre": genre,
                "note": "This is a placeholder - real music generation requires specialized AI models",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Music generation error: {str(e)}"
            }
    
    async def generate_sound_effect(
        self, 
        description: str,
        duration: float = 2.0
    ) -> Dict[str, Any]:
        """تولید افکت صوتی"""
        
        # شبیه‌سازی تولید افکت صوتی
        try:
            import wave
            import math
            import random
            
            sample_rate = 44100
            duration_samples = int(duration * sample_rate)
            samples = []
            
            # انواع مختلف افکت بر اساس توضیحات
            if "rain" in description.lower():
                # صدای باران
                for i in range(duration_samples):
                    noise = random.uniform(-0.1, 0.1)
                    samples.append(int(noise * 32767))
            
            elif "bell" in description.lower():
                # صدای زنگ
                frequency = 800
                for i in range(duration_samples):
                    t = i / sample_rate
                    amplitude = 0.5 * math.sin(2 * math.pi * frequency * t) * math.exp(-t*2)
                    samples.append(int(amplitude * 32767))
            
            else:
                # افکت عمومی
                frequency = 440
                for i in range(duration_samples):
                    t = i / sample_rate
                    amplitude = 0.3 * math.sin(2 * math.pi * frequency * t)
                    samples.append(int(amplitude * 32767))
            
            # ذخیره فایل
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sfx_{timestamp}.wav"
            filepath = Path("generated_audio") / filename
            filepath.parent.mkdir(exist_ok=True)
            
            with wave.open(str(filepath), 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(b''.join(sample.to_bytes(2, 'little', signed=True) for sample in samples))
            
            return {
                "success": True,
                "audio_path": str(filepath),
                "description": description,
                "duration": duration,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Sound effect generation error: {str(e)}"
            }


class VideoGenerator:
    """تولیدکننده ویدیو (محدود)"""
    
    def __init__(self):
        self.video_generation_available = False  # نیاز به ابزارهای پیشرفته
    
    async def create_slideshow(
        self, 
        images: List[str], 
        duration_per_image: float = 3.0,
        transition: str = "fade"
    ) -> Dict[str, Any]:
        """ایجاد اسلایدشو از تصاویر"""
        
        try:
            # این یک شبیه‌سازی است - در پیاده‌سازی واقعی باید از FFmpeg استفاده کرد
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path("generated_videos") / f"slideshow_{timestamp}.mp4"
            output_path.parent.mkdir(exist_ok=True)
            
            # شبیه‌سازی ایجاد ویدیو
            total_duration = len(images) * duration_per_image
            
            return {
                "success": True,
                "video_path": str(output_path),
                "images_used": images,
                "total_duration": total_duration,
                "transition": transition,
                "note": "This is a placeholder - real video generation requires FFmpeg",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Slideshow creation error: {str(e)}"
            }
    
    async def generate_animated_text(
        self, 
        text: str, 
        style: str = "typewriter",
        duration: float = 5.0
    ) -> Dict[str, Any]:
        """تولید انیمیشن متن"""
        
        # شبیه‌سازی - در پیاده‌سازی واقعی نیاز به ابزارهای انیمیشن دارد
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path("generated_videos") / f"text_animation_{timestamp}.mp4"
        output_path.parent.mkdir(exist_ok=True)
        
        return {
            "success": True,
            "video_path": str(output_path),
            "text": text,
            "style": style,
            "duration": duration,
            "note": "This is a placeholder for text animation",
            "timestamp": datetime.now().isoformat()
        }


class MediaCreator:
    """کلاس اصلی تولید محتوای چندرسانه‌ای"""
    
    def __init__(self):
        self.image_generator = ImageGenerator()
        self.audio_generator = AudioGenerator()
        self.video_generator = VideoGenerator()
        self.creation_history = []
    
    async def create_content(
        self, 
        content_type: str, 
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """تولید محتوا بر اساس نوع"""
        
        try:
            result = None
            
            if content_type == "image":
                result = await self.image_generator.generate_image(
                    prompt, 
                    kwargs.get("style", "realistic"),
                    kwargs.get("size", "1024x1024"),
                    kwargs.get("quality", "standard")
                )
            
            elif content_type == "speech":
                result = await self.audio_generator.generate_speech(
                    prompt,
                    kwargs.get("voice", "alloy"),
                    kwargs.get("speed", 1.0)
                )
            
            elif content_type == "music":
                result = await self.audio_generator.generate_music(
                    prompt,
                    kwargs.get("duration", 30),
                    kwargs.get("genre", "ambient")
                )
            
            elif content_type == "sound_effect":
                result = await self.audio_generator.generate_sound_effect(
                    prompt,
                    kwargs.get("duration", 2.0)
                )
            
            elif content_type == "slideshow":
                result = await self.video_generator.create_slideshow(
                    kwargs.get("images", []),
                    kwargs.get("duration_per_image", 3.0),
                    kwargs.get("transition", "fade")
                )
            
            elif content_type == "text_animation":
                result = await self.video_generator.generate_animated_text(
                    prompt,
                    kwargs.get("style", "typewriter"),
                    kwargs.get("duration", 5.0)
                )
            
            else:
                result = {
                    "success": False,
                    "error": f"Unsupported content type: {content_type}"
                }
            
            # ذخیره در تاریخچه
            if result:
                self.creation_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "content_type": content_type,
                    "prompt": prompt,
                    "result": result,
                    "parameters": kwargs
                })
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Content creation error: {str(e)}",
                "content_type": content_type,
                "prompt": prompt
            }
    
    async def batch_create(
        self, 
        requests: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """تولید دسته‌ای محتوا"""
        
        results = []
        
        for request in requests:
            content_type = request.get("content_type")
            prompt = request.get("prompt")
            params = request.get("parameters", {})
            
            result = await self.create_content(content_type, prompt, **params)
            results.append(result)
            
            # تأخیر کوتاه بین درخواست‌ها
            await asyncio.sleep(1)
        
        return results
    
    def get_creation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """دریافت تاریخچه تولیدات"""
        return self.creation_history[-limit:]
    
    def get_supported_content_types(self) -> Dict[str, List[str]]:
        """دریافت انواع محتوای پشتیبانی شده"""
        return {
            "image": ["realistic", "artistic", "cartoon", "abstract", "vintage", "minimalist", "fantasy"],
            "audio": ["speech", "music", "sound_effect"],
            "video": ["slideshow", "text_animation"],
            "parameters": {
                "image": ["style", "size", "quality"],
                "speech": ["voice", "speed"],
                "music": ["duration", "genre"],
                "sound_effect": ["duration"],
                "slideshow": ["images", "duration_per_image", "transition"],
                "text_animation": ["style", "duration"]
            }
        }
    
    async def enhance_content(
        self, 
        content_path: str, 
        enhancement_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """بهبود محتوای موجود"""
        
        try:
            if enhancement_type == "upscale_image":
                # بهبود کیفیت تصویر (شبیه‌سازی)
                return {
                    "success": True,
                    "original_path": content_path,
                    "enhanced_path": content_path.replace(".png", "_upscaled.png"),
                    "enhancement": "upscaled",
                    "note": "This is a placeholder for image upscaling"
                }
            
            elif enhancement_type == "noise_reduction":
                # کاهش نویز صوتی (شبیه‌سازی)
                return {
                    "success": True,
                    "original_path": content_path,
                    "enhanced_path": content_path.replace(".wav", "_denoised.wav"),
                    "enhancement": "noise_reduced",
                    "note": "This is a placeholder for audio noise reduction"
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported enhancement type: {enhancement_type}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Content enhancement error: {str(e)}"
            }
