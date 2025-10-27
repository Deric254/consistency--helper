import os
import requests
import json
import time

class AIIntegration:
    """Enhanced AI integration with FREE HuggingFace models"""
    
    def __init__(self, provider="huggingface", api_key=None, model="facebook/bart-large-cnn"):
        self.provider = provider.lower()
        self.api_key = api_key or os.getenv(f"{provider.upper()}_API_KEY")
        self.model = model
        
        if not self.api_key:
            print(f"⚠️  No API key found for {provider}. Using basic enhancement.")
            self.enabled = False
        else:
            self.enabled = True
            print(f"✅ AI Enhancement: {provider.upper()} - {model}")
    
    def enhance_post(self, post_text, platform, tone="empowering"):
        """Enhance post with AI for specific platform"""
        if not self.enabled:
            return self._basic_enhancement(post_text, platform)
        
        if self.provider == "huggingface":
            return self._huggingface_enhance(post_text, platform, tone)
        elif self.provider == "openai":
            return self._openai_enhance(post_text, platform, tone)
        elif self.provider == "cohere":
            return self._cohere_enhance(post_text, platform, tone)
        else:
            return self._basic_enhancement(post_text, platform)
    
    def _huggingface_enhance(self, post_text, platform, tone):
        """
        FREE Enhancement using HuggingFace Inference API
        Uses multiple models for best results
        """
        
        # Strategy: Use text generation model for enhancement
        models_to_try = [
            "mistralai/Mistral-7B-Instruct-v0.2",  # Best for instructions
            "facebook/bart-large-cnn",              # Good for text improvement
            "google/flan-t5-large"                  # Reliable fallback
        ]
        
        for model in models_to_try:
            try:
                enhanced = self._call_huggingface_model(model, post_text, platform, tone)
                if enhanced and len(enhanced) > 50:  # Valid response
                    return enhanced
            except Exception as e:
                print(f"⚠️  Model {model} failed, trying next...")
                continue
        
        # If all models fail, use rule-based enhancement
        print("⚠️  All AI models unavailable, using smart enhancement")
        return self._smart_enhancement(post_text, platform, tone)
    
    def _call_huggingface_model(self, model, post_text, platform, tone):
        """Call HuggingFace inference API"""
        
        API_URL = f"https://api-inference.huggingface.co/models/{model}"
        
        # Create enhancement prompt
        prompt = self._create_prompt(post_text, platform, tone)
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 300,
                "temperature": 0.7,
                "top_p": 0.9,
                "do_sample": True
            }
        }
        
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            # Handle different response formats
            if isinstance(result, list) and len(result) > 0:
                generated = result[0].get('generated_text', '')
                # Clean up the response
                return self._clean_generated_text(generated, prompt)
            elif isinstance(result, dict):
                return result.get('generated_text', post_text)
                
        elif response.status_code == 503:
            # Model is loading, wait and retry once
            print(f"⏳ Model loading, waiting 5 seconds...")
            time.sleep(5)
            response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    generated = result[0].get('generated_text', '')
                    return self._clean_generated_text(generated, prompt)
        
        return None
    
    def _create_prompt(self, post_text, platform, tone):
        """Create effective prompt for enhancement"""
        
        platform_tips = {
            "linkedin": "professional, add value-driven insights",
            "whatsapp": "conversational, friendly, use emojis",
            "facebook": "engaging, community-focused",
            "twitter": "concise, punchy, trending",
            "instagram": "visual, inspirational, hashtag-rich"
        }
        
        style = platform_tips.get(platform, "engaging")
        
        prompt = f"""Rewrite this {platform} post to be more {tone} and {style}:

Original: {post_text}

Enhanced version:"""
        
        return prompt
    
    def _clean_generated_text(self, generated, prompt):
        """Clean AI-generated text"""
        # Remove the prompt from response if present
        if prompt in generated:
            generated = generated.replace(prompt, "").strip()
        
        # Remove common artifacts
        generated = generated.replace("Enhanced version:", "").strip()
        generated = generated.replace("Rewritten:", "").strip()
        
        # Take only the first paragraph if too long
        if len(generated) > 800:
            generated = generated.split('\n\n')[0]
        
        return generated
    
    def _smart_enhancement(self, post_text, platform, tone):
        """
        Rule-based enhancement when AI unavailable
        Still makes posts better without API calls
        """
        
        # Platform-specific improvements
        enhancements = {
            "linkedin": {
                "prefix": "🚀 ",
                "suffix": "\n\n💡 What's your experience with this? Share below!",
                "hashtags": ["#DataAnalytics", "#BusinessIntelligence", "#ProfessionalGrowth"]
            },
            "whatsapp": {
                "prefix": "✨ ",
                "suffix": "\n\n📞 DM me to get started!",
                "hashtags": ["#DericBI", "#DataSkills"]
            },
            "facebook": {
                "prefix": "💡 ",
                "suffix": "\n\n👉 Tag someone who needs this!",
                "hashtags": ["#DataDriven", "#TechCareer", "#Analytics"]
            },
            "twitter": {
                "prefix": "⚡ ",
                "suffix": "\n\nRT if you agree 🔄",
                "hashtags": ["#DataScience", "#BI", "#TechTwitter"]
            },
            "instagram": {
                "prefix": "✨ ",
                "suffix": "\n\n💬 Double tap if this resonates!",
                "hashtags": ["#DataAnalytics", "#TechLife", "#CareerGrowth", "#DericBI"]
            }
        }
        
        config = enhancements.get(platform, enhancements["linkedin"])
        
        # Build enhanced post
        enhanced = f"{config['prefix']}{post_text}{config['suffix']}"
        
        # Add hashtags if not already present
        if not any(tag in post_text for tag in config['hashtags']):
            enhanced += "\n\n" + " ".join(config['hashtags'][:3])
        
        # Add tone-specific touches
        if tone == "empowering":
            power_words = [
                "Transform your", "Unlock your", "Master the art of",
                "Elevate your", "Supercharge your"
            ]
            # Try to inject power words naturally (basic logic)
            for word in power_words:
                if word.lower().split()[0] not in enhanced.lower():
                    enhanced = enhanced.replace("your", word, 1)
                    break
        
        return enhanced
    
    def _openai_enhance(self, post_text, platform, tone):
        """Enhance using OpenAI API (if user has key)"""
        prompt = f"""Enhance this {platform} post to be more {tone} and engaging.

Original:
{post_text}

Requirements:
- Keep it authentic and {tone}
- Add strategic emojis (max 3-4)
- Optimize for {platform}
- Strong call-to-action
- Keep under 500 characters

Enhanced:"""

        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": "You are a social media expert for tech professionals."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 400
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content'].strip()
                
        except Exception as e:
            print(f"⚠️  OpenAI error: {e}")
        
        return self._smart_enhancement(post_text, platform, tone)
    
    def _cohere_enhance(self, post_text, platform, tone):
        """Enhance using Cohere API (free tier available)"""
        prompt = f"""Make this {platform} post more {tone} and engaging:

{post_text}

Enhanced version:"""
        
        try:
            response = requests.post(
                "https://api.cohere.ai/v1/generate",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "command",
                    "prompt": prompt,
                    "max_tokens": 300,
                    "temperature": 0.7,
                    "stop_sequences": ["\n\n\n"]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['generations'][0]['text'].strip()
                
        except Exception as e:
            print(f"⚠️  Cohere error: {e}")
        
        return self._smart_enhancement(post_text, platform, tone)
    
    def _basic_enhancement(self, post_text, platform):
        """Fallback if no API configured"""
        emoji_map = {
            "whatsapp": "✨",
            "linkedin": "🚀",
            "facebook": "💡",
            "twitter": "⚡",
            "instagram": "✨"
        }
        emoji = emoji_map.get(platform, "")
        return f"{emoji} {post_text}\n\n[Enhanced for {platform}]"
    
    def generate_hashtags(self, content, count=5):
        """Generate relevant hashtags"""
        # Rule-based hashtag generation
        keywords = {
            "data": ["#DataAnalytics", "#DataScience", "#BigData"],
            "business": ["#BusinessIntelligence", "#BI", "#DataDriven"],
            "dashboard": ["#DataVisualization", "#Dashboards", "#Analytics"],
            "teach": ["#LearnData", "#DataEducation", "#SkillBuilding"],
            "audit": ["#DataAudit", "#BusinessAnalysis", "#Insights"]
        }
        
        content_lower = content.lower()
        selected = set()
        
        # Always include brand hashtags
        selected.add("#DericBI")
        
        # Add contextual hashtags
        for keyword, tags in keywords.items():
            if keyword in content_lower:
                selected.update(tags[:2])
        
        # Add generic tech hashtags if needed
        generic = ["#TechCareer", "#DataJobs", "#Analytics", "#TechSkills"]
        while len(selected) < count:
            for tag in generic:
                if tag not in selected:
                    selected.add(tag)
                    if len(selected) >= count:
                        break
        
        return list(selected)[:count]


# Quick test function
if __name__ == "__main__":
    print("\n🧪 Testing AI Integration...\n")
    
    # Test with sample post
    ai = AIIntegration(provider="huggingface", api_key=None)
    
    sample = "Learn Business Intelligence and transform your career with data analytics."
    
    print("Original Post:")
    print(sample)
    print("\n" + "="*60 + "\n")
    
    enhanced = ai.enhance_post(sample, "linkedin", "empowering")
    
    print("Enhanced Post:")
    print(enhanced)
    print("\n" + "="*60 + "\n")
    
    hashtags = ai.generate_hashtags(sample, 5)
    print("Generated Hashtags:")
    print(" ".join(hashtags))
