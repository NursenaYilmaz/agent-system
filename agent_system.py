from datetime import datetime
from transformers import pipeline
from collections import deque


class TextAnalyzerAgent:
    def __init__(self,name,message_queue):
        self.name=name
        self.message_queue=message_queue
        print(f"{self.name} Agent hazırlanıyor")

        self.toxicity_detector=pipeline(
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
            task="sentiment-analysis"  
        )
        print(f"{self.name} model hazır!")

    def process(self, input_data):
        text = input_data.get("text", "")
        if not text:
           return {"status": "error", "message": "metin yok"}
    
        result = self.toxicity_detector(text)
        analysis=result[0]
        label=analysis["label"]
        score=analysis["score"]

    
        if label == "negative":
          sentiment = "Negatif"
        elif label == "neutral":
          sentiment = "Nötr"
        else:  # positive
          sentiment = "Pozitif"


        confidence_percent = round(score * 100, 2)
        self.message_queue.send_message(
           sender=self.name,
           receiver="Rapor Agent",
           message_type="Analysis complete",
           content=f"Duygu: {sentiment}, Güven: %{confidence_percent}"
        )
        return {
        "status": "success",
        "original_text": text,
        "sentiment":sentiment,
        "confidence_score":confidence_percent,
        "label": label
        }



    
class ReportGeneratorAgent:
    def __init__(self,name,message_queue):
        self.name=name
        self.message_queue=message_queue
        print(f"Agent hazır:{self.name}")

    def process(self, input_data):
        incoming_messages = self.message_queue.get_messages_for(self.name)
        if incoming_messages:
           print(f"\n {self.name} mesajları okuyor:")
           for msg in incoming_messages:
             print(f"{msg['sender']}: {msg['content']}")
        status = input_data.get("status", "") 
        if status == "error":
            return {"status": "error", "message": "Önceki agenttan hata geldi"}
        
        self.message_queue.send_message(
        sender=self.name,
        receiver="Analiz Agent",
        message_type="REPORT_GENERATED",
        content="Rapor başarıyla oluşturuldu"
    )
           
        sentiment = input_data.get("sentiment", "")
        confidence_score = input_data.get("confidence_score", 0)
        original_text = input_data.get("original_text", "")
        label = input_data.get("label", "")
        emoji=input_data.get("emoji","")

        report = f"DUYGU ANALİZİ RAPORU\n Metin: {original_text}\n Duygu: {sentiment}\n Güven Skoru: %{confidence_score}"

        return {
        "status": "success",
        "report": report,
        "sentiment":sentiment,
        "agent_name": self.name
    }


class A2AManager:
    def __init__(self):
        self.message_queue = MessageQueue()  
        self.agent1 = TextAnalyzerAgent("Analiz Agent", self.message_queue)  
        self.agent2 = ReportGeneratorAgent("Rapor Agent", self.message_queue)  
        print(f"Agentlar hazır.")
    
    def run_pipeline(self, user_text):
        print(f"\n Pipeline başladı: {user_text}")
        self.message_queue.clear_messages() 
        
        input_data = {"text": user_text}
        agent1_output = self.agent1.process(input_data)
        agent2_output = self.agent2.process(agent1_output)
        
        print(f"\n {agent2_output['report']}")
        return agent2_output
    
class MessageQueue:
   def __init__(self):
      self.messages=deque()
    
   def send_message(self,sender,receiver,message_type,content):
      message={"sender":sender,
                "receiver":receiver,
                "message_type":message_type,
                "content":content,
                "timestamp":datetime.now()
      }
      self.messages.append(message)
      print(f"[{message['timestamp']}] {sender} -> {receiver}: {message_type}")
      
   def get_messages_for(self,receiver):
      received=[msg for msg in self.messages if msg["receiver"]==receiver]
      return received
   def clear_messages(self):
      self.messages.clear()
      
    
if __name__ == "__main__":
    manager = A2AManager()
    
    print("\n")
    print("TEST 1: Pozitif Metin")
    print("\n")
    manager.run_pipeline("I love this beautiful day!")
    
    print("\n")
    print("TEST 2: Negatif Metin")
    print("\n")
    manager.run_pipeline("I hate you, you are stupid!")
    
    print("\n")
    print("TEST 3: Nötr Metin")
    print("\n")
    manager.run_pipeline("I went to the store yesterday.")
    
    print("\n")
    print("TEST 4: Çok Pozitif Metin")
    print("\n")
    manager.run_pipeline("This is amazing! I'm so happy and excited!")
    
    print("\n")
    print("TEST 5: Çok Negatif Metin")
    print("\n")
    manager.run_pipeline("This is terrible and awful. I'm so disappointed.")




    
