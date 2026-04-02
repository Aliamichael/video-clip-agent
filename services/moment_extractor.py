import os
import json
from openai import OpenAI

class MomentExtractor:
    def __init__(self, ollama_url='http://localhost:11434'):
        self.ollama_url = ollama_url
        self.client = None

    def _get_openai_client(self):
        if self.client is None:
            api_key = os.getenv('OPENAI_API_KEY', '')
            if api_key:
                self.client = OpenAI(api_key=api_key)
        return self.client

    def extract_key_moments(self, transcript, job_id, use_local=True, num_moments=8):
        segments = transcript['segments']
        full_text = transcript['full_text']
        
        context = self._build_context(segments, max_chars=12000)
        
        if use_local:
            moments = self._extract_with_ollama(context, num_moments)
        else:
            moments = self._extract_with_openai(context, num_moments)
        
        return moments

    def _build_context(self, segments, max_chars=12000):
        context = []
        total_chars = 0
        
        for seg in segments:
            seg_text = f"[{self._format_time(seg['start'])}] {seg['text']}"
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
        prompt = f"""Analyze this transcript and identify the {num_moments} most engaging/impactful moments suitable for social media clips.

Context: Consider what makes content shareable:
- Emotionally impactful statements
- Key insights or revelations
- Memorable quotes
- Calls to action
- Surprising information
- Practical advice or steps

Transcript:
{context}

Extract exactly {num_moments} moments. Return as JSON array with this format:
[{{"start": seconds, "end": seconds, "title": "brief title", "reason": "why this is a good clip", "platform_score": {{"youtube": 0-10, "instagram": 0-10, "facebook": 0-10}}}}]

Make each clip 30-90 seconds long for optimal social media engagement. Consider content that stands on its own without heavy context."""

        client = self._get_openai_client()
        
        if not client:
            return self._extract_fallback_moments(context, num_moments)
        
        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert content curator for social media. Extract engaging moments from transcripts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            moments = result.get('moments', result.get('clips', []))
            
            return self._validate_moments(moments)
            
        except Exception as e:
            print(f"OpenAI extraction failed: {e}")
            return self._extract_fallback_moments(context, num_moments)

    def _extract_with_ollama(self, context, num_moments):
        prompt = f"""Analyze this transcript and identify the {num_moments} most engaging/impactful moments.

Transcript:
{context}

Return a JSON array with {num_moments} moments in this format (no markdown):
[{{"start": seconds, "end": seconds, "title": "brief title", "reason": "why this is a good clip", "platform_score": {{"youtube": 0-10, "instagram": 0-10, "facebook": 0-10}}}}]

Clips should be 30-90 seconds. Be selective - choose moments with emotional impact, key insights, memorable quotes, or calls to action."""

        try:
            import requests
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3",
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                moments = json.loads(result.get('response', '[]'))
                return self._validate_moments(moments)
        except Exception as e:
            print(f"Ollama extraction failed: {e}")
        
        return self._extract_fallback_moments(context, num_moments)

    def _extract_fallback_moments(self, context, num_moments):
        segments = context.split('\n')
        
        scored = []
        keywords = [
            'important', 'key', 'remember', 'notice', 'listen',
            'believe', 'truth', 'love', 'hope', 'faith', 'God',
            'Jesus', 'Christ', 'salvation', 'grace', 'mercy',
            'promise', 'blessing', 'power', 'spirit', 'heart'
        ]
        
        for seg in segments:
            if ']' not in seg:
                continue
                
            time_part = seg.split(']')[0].replace('[', '')
            parts = time_part.split(':')
            seconds = int(parts[0]) * 60 + int(parts[1])
            
            text_lower = seg.lower()
            score = sum(1 for kw in keywords if kw in text_lower)
            
            scored.append((seconds, score, seg.split(']')[1].strip()))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        
        moments = []
        used_times = []
        
        for seconds, score, text in scored:
            for used_start in used_times:
                if abs(seconds - used_start) < 45:
                    break
            else:
                used_times.append(seconds)
                
                platform_scores = {
                    'youtube': min(10, 5 + score),
                    'instagram': min(10, 6 + score) if len(text) < 150 else 5,
                    'facebook': min(10, 7 + score)
                }
                
                moments.append({
                    'start': max(0, seconds - 5),
                    'end': min(seconds + 60, seconds + 90),
                    'title': text[:60] + '...' if len(text) > 60 else text,
                    'reason': f'Contains key spiritual content (score: {score})',
                    'platform_score': platform_scores
                })
                
                if len(moments) >= num_moments:
                    break
        
        return moments

    def _validate_moments(self, moments):
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
                    'title': m.get('title', 'Clip')[:100],
                    'reason': m.get('reason', 'Key moment')[:200],
                    'platform_score': m.get('platform_score', {
                        'youtube': 7,
                        'instagram': 7,
                        'facebook': 7
                    })
                })
        
        validated.sort(key=lambda x: x['start'])
        return validated
