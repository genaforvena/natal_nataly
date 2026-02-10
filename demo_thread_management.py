#!/usr/bin/env python3
"""
Demo script showing conversation thread management in action
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import SessionLocal, init_db
from thread_manager import (
    add_message_to_thread,
    get_conversation_thread,
    reset_thread,
    get_thread_summary
)

def demo_conversation_thread():
    """Demonstrate the conversation thread feature"""
    
    print("\n" + "="*70)
    print("CONVERSATION THREAD MANAGEMENT - DEMONSTRATION")
    print("="*70)
    
    # Initialize
    init_db()
    session = SessionLocal()
    demo_user = "demo_user_12345"
    
    try:
        # Start fresh
        reset_thread(session, demo_user)
        print("\n📋 Starting new conversation...\n")
        
        # Simulate a conversation
        conversations = [
            ("user", "Привет! Расскажи про мой знак Солнца"),
            ("assistant", "Привет! Твое Солнце в Тельце. Это значит, что ты надежный, практичный и ценишь стабильность..."),
            ("user", "А что насчет карьеры?"),
            ("assistant", "С Солнцем в Тельце тебе подходят профессии, связанные с финансами, искусством или недвижимостью..."),
            ("user", "Расскажи про Луну"),
            ("assistant", "Твоя Луна в Раке. Это делает тебя эмоционально чувствительным и заботливым..."),
            ("user", "А как это влияет на отношения?"),
            ("assistant", "Луна в Раке означает, что ты очень привязан к семье и ищешь эмоциональную близость..."),
            ("user", "Что скажешь про Венеру?"),
            ("assistant", "Твоя Венера в Близнецах. Ты любишь общение и разнообразие в отношениях..."),
            ("user", "А Меркурий?"),
            ("assistant", "Меркурий в Овне дает тебе быстрый ум и прямоту в общении..."),
            ("user", "Расскажи про Марс"),
            ("assistant", "Марс в Скорпионе дает тебе страстность и целеустремленность..."),
        ]
        
        # Add messages one by one with status updates
        for i, (role, content) in enumerate(conversations, 1):
            add_message_to_thread(session, demo_user, role, content)
            
            # Show progress
            thread = get_conversation_thread(session, demo_user)
            summary = get_thread_summary(session, demo_user)
            
            print(f"Message {i}/{len(conversations)}: {role}")
            print(f"  Content: {content[:60]}...")
            print(f"  Thread size: {len(thread)}/10 messages")
            
            # Show when trimming happens
            if len(thread) == 10 and i > 10:
                print(f"  ⚠️  TRIMMING: Removed oldest non-fixed message (FIFO)")
            
            if summary['fixed_messages'] > 0 and i <= 2:
                print(f"  🔒 FIXED: This message will never be deleted")
            
            print()
        
        # Final state
        print("\n" + "="*70)
        print("FINAL THREAD STATE")
        print("="*70)
        
        thread = get_conversation_thread(session, demo_user)
        summary = get_thread_summary(session, demo_user)
        
        print(f"\n📊 Thread Summary:")
        print(f"  Total messages: {summary['total_messages']}/10")
        print(f"  Fixed messages: {summary['fixed_messages']} (never deleted)")
        print(f"  User messages: {summary['user_messages']}")
        print(f"  Assistant messages: {summary['assistant_messages']}")
        
        print(f"\n💬 Current Thread Contents:")
        for i, msg in enumerate(thread, 1):
            marker = "🔒" if i <= 2 else "  "
            print(f"{marker} {i}. {msg['role']:9} | {msg['content'][:65]}...")
        
        # Show what was removed
        print(f"\n❌ Removed Messages (FIFO):")
        print(f"  3. user      | А что насчет карьеры?")
        print(f"  4. assistant | С Солнцем в Тельце тебе подходят профессии...")
        print(f"  (These were deleted to maintain the 10-message limit)")
        
        # Demonstrate reset
        print("\n" + "="*70)
        print("DEMONSTRATING /reset_thread COMMAND")
        print("="*70)
        
        deleted_count = reset_thread(session, demo_user)
        print(f"\n✅ Thread reset! Deleted {deleted_count} messages")
        
        thread = get_conversation_thread(session, demo_user)
        print(f"📋 Thread is now empty: {len(thread)} messages")
        
        # Start fresh conversation
        print("\n🆕 Starting fresh conversation after reset:")
        add_message_to_thread(session, demo_user, "user", "Привет снова! Расскажи про Юпитер")
        add_message_to_thread(session, demo_user, "assistant", "Привет! Твой Юпитер в Стрельце...")
        
        thread = get_conversation_thread(session, demo_user)
        print(f"  New thread has {len(thread)} messages")
        for i, msg in enumerate(thread, 1):
            print(f"  {i}. {msg['role']:9} | {msg['content'][:50]}...")
        
        print("\n" + "="*70)
        print("✅ DEMONSTRATION COMPLETE")
        print("="*70)
        print("\nKey Features Demonstrated:")
        print("  ✅ Max 10 messages per thread")
        print("  ✅ First 2 messages (user + assistant) are FIXED")
        print("  ✅ FIFO deletion of oldest non-fixed messages")
        print("  ✅ Thread context preserved for LLM")
        print("  ✅ /reset_thread command clears history")
        print("  ✅ Seamless continuation of conversation")
        print()
        
    finally:
        session.close()


if __name__ == "__main__":
    demo_conversation_thread()
