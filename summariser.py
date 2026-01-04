import re
import ssl
ssl._create_default_https_context = ssl._create_unverified_context  

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from transformers import pipeline


def get_video_id(url):
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11})',
        r'(?:youtube\.com\/watch\?v=)([^&]{11})',
        r'(?:youtu\.be\/)([^?]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_transcript(video_id):
    """YOUR ORIGINAL WORKING VERSION - UNCHANGED"""
    try:
        print(f"📥 Fetching transcript for: {video_id}")
        ytt_api = YouTubeTranscriptApi()
        fetched_transcript = ytt_api.fetch(video_id)
        print(f"✅ Found transcript!")
        text_parts = [snippet.text for snippet in fetched_transcript] 
        text = " ".join(text_parts)
        text = text.replace('\n', ' ')
        text = ' '.join(text.split())
        print(f"✅ Got {len(fetched_transcript)} entries, {len(text)} chars")
        return text
    except TranscriptsDisabled:
        print("❌ Transcripts disabled")
        return None
    except NoTranscriptFound:
        print("❌ No transcript")
        return None
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        try:
            print("🔄 English fallback...")
            ytt_api = YouTubeTranscriptApi()
            fetched_transcript = ytt_api.fetch(video_id, languages=['en', 'en-US', 'en-GB'])
            text_parts = [snippet.text for snippet in fetched_transcript]
            text = " ".join(text_parts)
            text = text.replace('\n', ' ')
            text = ' '.join(text.split())
            print(f"✅ Fallback: {len(text)} chars")
            return text
        except:
            return None


def summarize_transcript(filename):
    """Fast AI summaries with SSL workaround"""
    import os
    os.environ['CURL_CA_BUNDLE'] = '' 
    
    try:
        print("🤖 AI loading (this may take a minute on first run)...")

        summarizer = pipeline("summarization", model="t5-small") 
        
        with open(filename, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Limit text to avoid crashing the tiny model (first 2000 chars)
        content_to_summarize = text[:2000]
        
        # Break into smaller chunks for the small T5 model
        chunks = [content_to_summarize[i:i+500] for i in range(0, len(content_to_summarize), 500)]
        print("\n📝 5-BULLET SUMMARY:")
        
        summary_list = []
        for chunk in chunks:
            if len(chunk.strip()) > 20: # skip tiny fragments
                summary = summarizer(chunk, max_length=40, min_length=10, do_sample=False)[0]['summary_text']
                bullet = f"• {summary.capitalize()}"
                print(bullet)
                summary_list.append(bullet)
        
        # Save Markdown
        summary_file = filename.replace('.txt', '_summary.md')
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"# Summary of {filename}\n\n" + "\n".join(summary_list))
        print(f"\n💾 {summary_file} saved!")
        
    except Exception as e:
        print(f"❌ Summary failed: {e}")


def main():
    print("="*60)
    print("✅ WORKING VERSION - Transcript + Summary")
    print("="*60)
    
    while True:
        print("-"*60)
        url = input("YouTube URL (quit): ").strip()
        
        if url.lower() in ['quit', 'q']:
            break
        
        video_id = get_video_id(url)
        if not video_id:
            print("❌ Invalid URL")
            continue
        
        print(f"🎬 ID: {video_id}")
        transcript = get_transcript(video_id)
        
        if transcript:
            print("\n" + "="*60)
            print("PREVIEW (500 chars):")
            print("="*60)
            print(transcript[:500])
            if len(transcript) > 500:
                print("... [continues] ...")
            print(f"\n📊 {len(transcript)} chars")
            
            save = input("\n💾 Save + Summary? (y/n): ").lower()
            if save == 'y':
                filename = f"transcript_{video_id}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(transcript)
                print(f"✅ Saved: {filename}")
                summarize_transcript(filename)
        else:
            print("❌ No transcript")
        
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋")
    input("\nPress Enter...")
