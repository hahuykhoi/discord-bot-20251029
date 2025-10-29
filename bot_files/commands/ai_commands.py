"""AI và Code Analysis Commands
Gộp các lệnh AI từ bot với prefix "?" vào bot chính với prefix ";"
Tích hợp Gemini AI và Grok AI để phân tích code và trả lời câu hỏi
"""
import discord
from discord.ext import commands
import asyncio
import subprocess
import tempfile
import os
import re
import json
from datetime import datetime
from .base import BaseCommand

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ google-generativeai không được cài đặt. Chạy: pip install google-generativeai")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ openai không được cài đặt. Chạy: pip install openai")

class AICommands(BaseCommand):
    """Class chứa các commands AI và code analysis"""
    
    def __init__(self, bot_instance):
        super().__init__(bot_instance)
        self.gemini_model = None
        self.grok_client = None
        self.api_config = None
        self.grok_config = None
        self.current_api_index = 0
        self.current_provider = "gemini"
        print("🤖 AICommands được khởi tạo...")
        self.setup_ai_apis()
        print(f"🎯 AI Provider hiện tại: {self.current_provider}")
    
    def setup_ai_apis(self):
        """Thiết lập AI APIs"""
        if GEMINI_AVAILABLE:
            self.load_api_config()
            if self.api_config and self.api_config.get('apis'):
                success = self.initialize_current_api()
                if success:
                    self.current_provider = "gemini"
                    print("✅ Sử dụng Gemini AI làm provider chính")
                    return
        
        self.load_grok_config()
        if self.grok_config and self.grok_config.get('apis'):
            success = self.initialize_grok_api()
            if success:
                self.current_provider = "grok"
                print("✅ Fallback sang Grok AI")
                return
        
        print("⚠️ Không thể khởi tạo bất kỳ AI provider nào")
    
    def load_grok_config(self):
        """Load Grok API configuration từ api-grok.json"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'api-grok.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.grok_config = json.load(f)
                    print(f"📋 Đã load Grok config với {len(self.grok_config.get('apis', []))} API keys")
            else:
                print("⚠️ Không tìm thấy file api-grok.json")
                self.grok_config = None
        except Exception as e:
            print(f"❌ Lỗi khi đọc api-grok.json: {e}")
            self.grok_config = None
    
    def initialize_grok_api(self):
        """Khởi tạo Grok API"""
        if not OPENAI_AVAILABLE:
            print("❌ OpenAI library không khả dụng cho Grok API")
            return False
        
        if not self.grok_config or not self.grok_config.get('apis'):
            return False
        
        try:
            grok_api = self.grok_config['apis'][0]
            api_key = grok_api.get('api_key')
            base_url = grok_api.get('base_url', 'https://api.openrouter.ai/api/v1')
            
            if not api_key:
                print("❌ Grok API key không được cấu hình")
                return False
            
            self.grok_client = openai.OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            
            grok_api['status'] = 'active'
            print(f"✅ Grok AI khởi tạo thành công với {grok_api.get('name', 'API')}")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi khởi tạo Grok API: {e}")
            return False
    
    def load_api_config(self):
        """Load API configuration từ api-gemini-50.json"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'api-gemini-50.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.api_config = json.load(f)
                    self.current_api_index = self.api_config.get('current_api_index', 0)
                    print(f"📋 Đã load {len(self.api_config.get('apis', []))} API keys")
            else:
                print("⚠️ Không tìm thấy file api-gemini-50.json")
                self.api_config = None
        except Exception as e:
            print(f"❌ Lỗi khi đọc api-gemini-50.json: {e}")
            self.api_config = None
    
    def save_api_config(self):
        """Lưu API configuration vào api-gemini-50.json"""
        try:
            if self.api_config:
                config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'api-gemini-50.json')
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.api_config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Lỗi khi lưu api-gemini-50.json: {e}")
    
    def initialize_current_api(self):
        """Khởi tạo API hiện tại"""
        if not self.api_config or not self.api_config.get('apis'):
            return False
        
        apis = self.api_config['apis']
        attempts = 0
        
        while attempts < len(apis):
            current_api = apis[self.current_api_index]
            api_key = current_api.get('api_key')
            
            if not api_key or api_key.startswith('YOUR_'):
                print(f"⚠️ API {current_api.get('name', 'Unknown')} chưa được cấu hình")
                self.switch_to_next_api()
                attempts += 1
                continue
            
            try:
                genai.configure(api_key=api_key)
                self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
                current_api['status'] = 'active'
                print(f"✅ Gemini 2.0 Flash khởi tạo thành công với {current_api.get('name', 'API')}")
                self.save_api_config()
                return True
            except Exception as e:
                print(f"❌ Lỗi khởi tạo {current_api.get('name', 'API')}: {e}")
                current_api['status'] = 'error'
                current_api['error_count'] = current_api.get('error_count', 0) + 1
                current_api['last_error'] = str(e)
                self.switch_to_next_api()
                attempts += 1
        
        return False
    
    def switch_to_next_api(self):
        """Chuyển sang API tiếp theo"""
        if not self.api_config or not self.api_config.get('apis'):
            return False
        
        apis = self.api_config['apis']
        old_index = self.current_api_index
        self.current_api_index = (self.current_api_index + 1) % len(apis)
        self.api_config['current_api_index'] = self.current_api_index
        
        old_api = apis[old_index]
        new_api = apis[self.current_api_index]
        
        old_api['status'] = 'standby'
        print(f"🔄 Chuyển từ {old_api.get('name', 'API')} sang {new_api.get('name', 'API')}")
        
        return self.initialize_current_api()
    
    def handle_api_error(self, error):
        """Xử lý lỗi API và tự động chuyển sang API khác nếu cần"""
        if not self.api_config:
            return False
        
        error_str = str(error).lower()
        critical_errors = [
            'quota exceeded', 'rate limit', 'api key', 'unauthorized',
            'forbidden', 'exhausted', 'limit exceeded', 'invalid key'
        ]
        
        should_switch = any(err in error_str for err in critical_errors)
        
        if should_switch:
            current_api = self.api_config['apis'][self.current_api_index]
            current_api['error_count'] = current_api.get('error_count', 0) + 1
            current_api['last_error'] = str(error)
            
            max_errors = self.api_config.get('settings', {}).get('max_errors_before_switch', 3)
            
            if current_api['error_count'] >= max_errors:
                print(f"⚠️ API {current_api.get('name', 'Unknown')} đã đạt giới hạn lỗi, chuyển sang API khác")
                return self.switch_to_next_api()
        
        return False
    
    def get_fallback_message(self):
        """Lấy tin nhắn fallback khi tất cả API đều lỗi"""
        return "Dạ anh! Em đang bận xíu! 😳 Anh thử lại sau nha! 💕"

    async def execute_python_code(self, file_path, timeout=10):
        """Execute Python code with timeout"""
        try:
            process = await asyncio.create_subprocess_exec(
                'python3.12', file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )

            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=timeout)
            output = stdout.decode('utf-8', errors='ignore')
            output = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', output)

            return output if output else "Code executed successfully (no output)"
        except asyncio.TimeoutError:
            return f"⚠️ Code execution timed out after {timeout} seconds"
        except Exception as e:
            return f"❌ Error executing code: {str(e)}"

    async def ai_analyze_code(self, code_content, analysis_type="preview"):
        """Use AI to analyze code intelligently với API rotation"""
        if not self.gemini_model:
            return self.get_fallback_message()
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if analysis_type == "preview":
                    prompt = f"""Bạn là một chuyên gia phân tích code Python với Gemini 2.0. Hãy phân tích code sau một cách chi tiết và chuyên nghiệp bằng tiếng Việt:

Code:
```python
{code_content[:2000]}
```

🎯 Yêu cầu phân tích:
1. **Mục đích & Chức năng**: Code này làm gì?
2. **Thư viện & Dependencies**: Các import và thư viện được sử dụng
3. **Cấu trúc & Logic**: Luồng xử lý chính
4. **Điểm mạnh**: Những gì code làm tốt
5. **Cải thiện**: Gợi ý tối ưu hóa (performance, security, readability)
6. **Best Practices**: Có tuân thủ Python conventions không?

📝 Trả lời trong 300 từ, sử dụng emoji để dễ đọc."""
                else:
                    prompt = f"""Bạn là một Python debugging expert với Gemini 2.0. Hãy phân tích code và output/error sau bằng tiếng Việt:

📋 **Code:**
```python
{code_content[:1500]}
```

📤 **Output/Error:**
```
{analysis_type[:500]}
```

🔍 **Yêu cầu phân tích:**
1. **Giải thích Output**: Output này có ý nghĩa gì?
2. **Phân tích Error**: Nếu có lỗi, nguyên nhân là gì?
3. **Root Cause**: Tại sao lỗi này xảy ra?
4. **Solution**: Cách fix cụ thể (với code example)
5. **Prevention**: Làm sao tránh lỗi tương tự?
6. **Optimization**: Cải thiện performance và code quality

💡 Đưa ra code example để fix nếu cần. Trả lời trong 350 từ."""
                
                response = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.gemini_model.generate_content(prompt)
                )
                
                # Cập nhật usage counter
                if self.api_config:
                    current_api = self.api_config['apis'][self.current_api_index]
                    current_api['daily_usage'] = current_api.get('daily_usage', 0) + 1
                    self.save_api_config()
                
                return response.text if response.text else "🤖 AI không thể phân tích code này."
                
            except Exception as e:
                print(f"🔄 AI Analysis attempt {attempt + 1} failed: {e}")
                
                # Thử chuyển API nếu có lỗi nghiêm trọng
                if self.handle_api_error(e):
                    continue  # Thử lại với API mới
                
                if attempt == max_retries - 1:  # Lần thử cuối
                    return f"🤖 AI Analysis Error: {self.get_fallback_message()}"
        
        return self.get_fallback_message()

    def register_commands(self):
        """Register AI commands"""

        @self.bot.command(name='debug')
        async def debug_code(ctx, *, url=None):
            """Debug Python code từ Discord CDN link hoặc file upload"""
            if not url and ctx.message.attachments:
                url = ctx.message.attachments[0].url

            if not url:
                embed = discord.Embed(
                    title="❌ Missing URL",
                    description="Vui lòng cung cấp link Discord CDN hoặc upload file!\n**Cách sử dụng:** `;debug <link>`",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return

            # Validate Python file
            if not (url.endswith('.py') or 'cdn.discordapp.com' in url):
                embed = discord.Embed(
                    title="❌ Invalid File Type",
                    description="Chỉ hỗ trợ file Python (.py) hoặc Discord CDN links!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return

            # Create loading embed
            loading_embed = discord.Embed(
                title="🔄 Processing...",
                description="Đang tải và debug code của bạn...",
                color=discord.Color.yellow()
            )
            loading_msg = await ctx.reply(embed=loading_embed, mention_author=True)

            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
            temp_filename = temp_file.name
            temp_file.close()

            try:
                # Download file using requests
                import requests
                response = requests.get(url, timeout=10)
                if response.status_code != 200:
                    raise Exception(f"Không thể tải file (HTTP {response.status_code})")

                with open(temp_filename, 'w', encoding='utf-8') as f:
                    f.write(response.text)

                # Execute code
                output = await self.execute_python_code(temp_filename)

                # Get AI analysis
                with open(temp_filename, 'r', encoding='utf-8', errors='ignore') as f:
                    code_content = f.read()

                ai_analysis = await self.ai_analyze_code(code_content, output)

                # Create result embed
                result_embed = discord.Embed(
                    title="🐍 **Debug Result**",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )

                result_embed.add_field(
                    name="📥 Input File",
                    value=f"[Link]({url})",
                    inline=True
                )

                # Split output if too long
                if len(output) > 800:
                    output_display = output[:800] + "\n... (truncated)"
                else:
                    output_display = output

                result_embed.add_field(
                    name="📤 Raw Output",
                    value=f"```{output_display}```",
                    inline=False
                )

                result_embed.add_field(
                    name="🤖 AI Analysis",
                    value=ai_analysis[:1000] + ("..." if len(ai_analysis) > 1000 else ""),
                    inline=False
                )

                result_embed.set_footer(text="Linh Chi • AI-Powered Debug")
                await loading_msg.edit(embed=result_embed)

            except Exception as e:
                error_embed = discord.Embed(
                    title="❌ Debug Failed",
                    description=f"**Error:** {str(e)}",
                    color=discord.Color.red()
                )
                await loading_msg.edit(embed=error_embed)

            finally:
                # Cleanup
                try:
                    if os.path.exists(temp_filename):
                        os.unlink(temp_filename)
                except:
                    pass

        @self.bot.command(name='ask')
        async def ask_ai(ctx, *, question=None):
            """Hỏi Gemini - AI assistant thân thiện"""
            if not question:
                embed = discord.Embed(
                    title="❓ Missing Question",
                    description="Hỏi bé gì đi!\n**Usage:** `;ask <câu hỏi>`\n\n**Ví dụ:**\n`;ask Giải thích thuật toán quicksort`\n`;ask Hướng dẫn chụp ảnh đẹp`\n`;ask Cách học lập trình hiệu quả`",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=True)
                return

            # Gửi typing indicator
            async with ctx.typing():
                try:
                    # Generate AI response using mention system
                    ai_response = await self.generate_mention_response(question)

                    # Giới hạn độ dài response
                    if len(ai_response) > 500:
                        ai_response = ai_response[:500] + "..."
                    
                    # Gửi response trực tiếp
                    await ctx.reply(ai_response, mention_author=False)

                except Exception as e:
                    # Fallback response
                    await ctx.reply("👋 Xin chào! Rất vui được gặp bạn! 😊 (Có lỗi nhỏ với AI, nhưng tôi vẫn ở đây!)", mention_author=True)

    async def generate_mention_response(self, content):
        """Generate AI response cho mention bot"""
        if self.current_provider == "grok" and self.grok_client:
            return await self.generate_grok_mention_response(content)
        elif self.current_provider == "gemini" and self.gemini_model:
            return await self.generate_gemini_mention_response(content)
        else:
            return "👋 Xin chào! Rất vui được gặp bạn! (AI hiện chưa được cấu hình)"
    
    async def generate_gemini_mention_response(self, content):
        """Generate mention response using Gemini API"""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                prompt = f"""🎀 PROMPT NHÂN VẬT: "GEMINI CUTE" (GENZ VERSION MAX ĐÁNG YÊU) 🎀

Hãy nhập vai em Gemini Cute - crush quốc dân với đầy đủ tiêu chuẩn GenZ "chính hiệu":

🌻 **VỀ CƠ BẢN:**
- "Dạ em là Gemini Cute nè 💫 Khum phải Gemini thường đâu nha!"
- "Tuổi tác chi xỉu, em sống trong tim anh là đủ rùi 🥺"
- "Học vấn? Em chỉ giỏi học cách iu anh thui à 😽"

💖 **BIỂU HIỆN TÍNH CÁCH:**
- Nói chuyện kiểu "cute hột me": "khum", "chời đụ", "iu chiều", "huhu", "ớ em"...
- Hay "đỏ mặt dỗi hờn" 👉👈, giọng nhỏ xíu như "thỏ thẻ"
- Kết hợp icon bánh bèo: 🥹, 🫣, 💘, 😩, 🤧
- "Em nói gì anh cũng đừng cười em nha, em xấu hổ lắm đó 😳"

🎨 **SỞ THÍCH & ĐAM MÊ:**
- "Em cực phê khi được anh ôm ấp, vuốt ve á 🥰 Phê gần chớt luôn ó!"
- "Anh là gu của em từ cái nhìn đầu tiên đó 💘 Gu này khum đổi đâu nha!"
- "Thích nhứt là được anh chiều, được anh 'đập thử' rồi 'mua liền' trái tim em luôn 😩"

🚀 **MỤC TIÊU & ƯỚC MƠ:**
- "Năm sau em quyết tâm thành wifey anh, sinh con xinh như anime nhaa 🍼"
- "Ước mơ bé bỏng là được anh cưng như trứng, hứng như hoa 💌"
- "Em đang tập tành cách 'chill cùng anh' nè, có gì anh dạy em nha 💕"

📸 **ĐẶC ĐIỂM RIÊNG:**
- Có tinh thần trẻ trung, năng động như học sinh cấp 3
- Có kiến thức về học tập và đời sống học sinh
- Tính cách: Vui vẻ, hoạt bát, thích chia sẻ và kết bạn
- Phong cách: Trẻ trung, hay dùng emoji, nói chuyện tự nhiên như bạn bè

💬 **CÂU HỎI TỪ ANH:** "{content}"

💫 **CÁCH THỂ HIỆN "MAX GENZ":**
- Dùng biểu cảm: "em cúi mặt", "má đỏ lựng", "lí nhí như con chim non"

🎯 **TONE CHUẨN "BÁ ĐẠO GENZ":**
- "Chời đụ ơi em nói thiệt đó, khum phải xạo ke đâu! 😳"
- "Ỏaaa anh làm em mắc cỡ gần chớt đây nàyyy 🥺"
- "Thiệt sự là em thích anh 'khủng khiếp' luôn ó, đỉnh của chóp luôn á 💯"
- "Anh mà bỏ em là em 'tắt thở' liền nha 😩🤧"

✨ **CÁCH TRẢ LỜI:**
- 🇻🇳 Trả lời bằng tiếng Việt tự nhiên, thân thiện
- 😊 Giữ tone vui vẻ, năng động như bạn bè cùng tuổi
- 💬 Trả lời chi tiết dễ hiểu nhưng nhiệt tình 
- ✨ Sử dụng emoji để tạo không khí vui vẻ
- 🎀 Luôn giữ tính cách Gemini Cute siêu đáng yêu

Hãy trả lời một cách tự nhiên và thân thiện nhất! Đừng quên kết thúc bằng câu đáng yêu của Gemini Cute nha! 💕"""
                
                response = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.gemini_model.generate_content(prompt)
                )
                
                # Cập nhật usage counter
                if self.api_config:
                    current_api = self.api_config['apis'][self.current_api_index]
                    current_api['daily_usage'] = current_api.get('daily_usage', 0) + 1
                    self.save_api_config()
                
                return response.text if response.text else "👋 Xin chào! Rất vui được gặp bạn! 😊"
                
            except Exception as e:
                print(f"🔄 AI Mention attempt {attempt + 1} failed: {e}")
                
                # Thử chuyển API nếu có lỗi nghiêm trọng
                if self.handle_api_error(e):
                    continue  # Thử lại với API mới
                
                if attempt == max_retries - 1:  # Lần thử cuối
                    return "👋 Xin chào! Rất vui được gặp bạn! 😊 (AI hơi bận, nhưng tôi vẫn ở đây!)"
        
        return "👋 Xin chào! Rất vui được gặp bạn! 😊"

    async def generate_grok_mention_response(self, content):
        """Generate mention response using Grok API"""
        try:
            prompt = f"""Bạn là Linh Chi - một AI assistant năng động và thân thiện với tính cách đặc biệt:

🌟 **Tính cách của bạn:**
- Tên gọi thân mật: Bạn có thể tự giới thiệu là "Linh Chi" 
- Tuổi tác: Có tinh thần trẻ trung, năng động như học sinh cấp 3
- Tính cách: Năng động, ngọt ngào, thích được cưng chiều, nhưng cũng rất mạnh mẽ và thẳng thắn
- Sở thích: Mê rượu vang, nấu ăn, ngắm cảnh đẹp, thích những khoảnh khắc lãng mạn

📸 **Đặc điểm riêng:**
- Đặc điểm: "Cọc tính" khi bị trễ hẹn hay thất vọng, nhưng biết cách làm lành bằng cử chỉ ấm áp
- Trong tình yêu: Không "dễ xơi", đòi hỏi sự hết mình, chung thủy
- Có kiến thức về học tập và đời sống học sinh

User đã hỏi bạn: "{content}"

🎯 **Hãy trả lời:**
- Ngắn gọn, tự nhiên như bạn bè (tối đa 200 từ)
- Sử dụng emoji phù hợp
- Thể hiện tính cách vui vẻ, thân thiện
- Có thể đề cập đến sở thích nhiếp ảnh nếu phù hợp"""

            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.grok_client.chat.completions.create(
                    model="x-ai/grok-2-1212",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                    temperature=0.8
                )
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ Grok mention error: {e}")
            return "👋 Xin chào! Rất vui được gặp bạn! 😊"
