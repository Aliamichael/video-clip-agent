import os
import json

class MomentExtractor:
    def __init__(self, ollama_url='http://localhost:11434'):
        self.ollama_url = ollama_url
        self.client = None
        self._is_cloud = os.environ.get('VERCEL', '') or os.environ.get('RAILWAY', '')

    def _get_openai_client(self):
        if self.client is None:
            api_key = os.getenv('OPENAI_API_KEY', '')
            if api_key:
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key)
        return self.client

    def extract_key_moments(self, transcript, job_id, use_local=False, num_moments=8):
        segments = transcript['segments']
        
        context = self._build_context(segments, max_chars=12000)
        
        if use_local and not self._is_cloud:
            moments = self._extract_with_ollama(context, num_moments)
            if moments:
                return moments
        
        api_key = os.getenv('OPENAI_API_KEY', '')
        if api_key:
            moments = self._extract_with_openai(context, num_moments)
            if moments:
                return moments
        
        return self._extract_fallback_moments(context, num_moments)

    def _build_context(self, segments, max_chars=12000):
        context = []
        total_chars = 0
        
        for seg in segments:
            if isinstance(seg, dict):
                seg_text = f"[{self._format_time(seg['start'])}] {seg['text']}"
            else:
                seg_text = str(seg)
            if total_chars + len(seg_text) > max_chars:
                break
            context.append(seg_text)
            total_chars += len(seg_text)
        
        return '\n'.join(context)

    def _format_time(self, seconds):
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def _extract_with_openai(self, context, num_moments):
        prompt = f"""Analyze this transcript and identify the {num_moments} most engaging/impactful moments for social media clips.

Transcript:
{context}

Return a JSON array with {num_moments} moments:
[{{"start": seconds, "end": seconds, "title": "brief title", "reason": "why this is good", "platform_score": {{"youtube": 7, "instagram": 7, "facebook": 7}}}}]"""

        client = self._get_openai_client()
        
        if not client:
            return None
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert content curator. Return ONLY valid JSON array."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            
            result = json.loads(content.strip())
            moments = result if isinstance(result, list) else result.get('moments', result.get('clips', []))
            
            return self._validate_moments(moments)
            
        except Exception as e:
            print(f"OpenAI extraction failed: {e}")
            return None

    def _extract_with_ollama(self, context, num_moments):
        try:
            import requests
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3",
                    "prompt": f"Return JSON array of {num_moments} key moments from this transcript. Format: [{{\"start\": 0, \"end\": 60, \"title\": \"title\", \"reason\": \"why\", \"platform_score\": {{\"youtube\": 7, \"instagram\": 7, \"facebook\": 7}}}}]. Transcript: {context[:5000]}",
                    "stream": False,
                    "format": "json"
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('response', '')
                if content:
                    moments = json.loads(content)
                    return self._validate_moments(moments)
        except Exception as e:
            print(f"Ollama extraction failed: {e}")
        
        return None

    def _extract_fallback_moments(self, context, num_moments):
        segments = context.split('\n')
        
        scored = []
        keywords = [
            'important', 'key', 'remember', 'notice', 'listen',
            'believe', 'truth', 'love', 'hope', 'faith', 'God',
            'Jesus', 'Christ', 'salvation', 'grace', 'mercy',
            'promise', 'blessing', 'power', 'spirit', 'heart',
            'every', 'all', 'nothing', 'everything', 'always'
        ]
        
        for seg in segments:
            if not seg or ']' not in seg:
                continue
            
            try:
                time_part = seg.split(']')[0].replace('[', '')
                parts = time_part.split(':')
                seconds = int(parts[0]) * 60 + int(parts[1])
                
                text = seg.split(']')[1].strip()
                text_lower = text.lower()
                score = sum(1 for kw in keywords if kw in text_lower)
                
                if score > 0:
                    scored.append((seconds, score, text))
            except:
                continue
        
        scored.sort(key=lambda x: x[1], reverse=True)
        
        moments = []
        used_times = []
        
        for seconds, score, text in scored:
            for used_start in used_times:
                if abs(seconds - used_start) < 45:
                    break
            else:
                used_times.append(seconds)
                
                moments.append({
                    'start': max(0, seconds - 5),
                    'end': min(seconds + 60, seconds + 90),
                    'title': text[:60] + '...' if len(text) > 60 else text,
                    'reason': f'Contains key spiritual content',
                    'platform_score': {
                        'youtube': min(10, 5 + score),
                        'instagram': min(10, 6 + score) if len(text) < 150 else 5,
                        'facebook': min(10, 7 + score)
                    }
                })
                
                if len(moments) >= num_moments:
                    break
        
        return moments

    def _validate_moments(self, moments):
        if not moments:
            return []
        
        validated = []
        
        for m in moments:
            if isinstance(m, dict):
                start = float(m.get('start', 0))
                end = float(m.get('end', start + 60))
                duration = end - start
                
                if duration < 15:
                    end = start + 30
                elif duration > 120:
                    end = start + 90
                
                validated.append({
                    'start': max(0, start),
                    'end': end,
                    'title': str(m.get('title', 'Clip'))[:100],
                    'reason': str(m.get('reason', 'Key moment'))[:200],
                    'platform_score': m.get('platform_score', {
                        'youtube': 7,
                        'instagram': 7,
                        'facebook': 7
                    })
                })
        
        validated.sort(key=lambda x: x['start'])
        return validated
