# Main.py

from Frontend.GUI import (  
    GraphicalUserInterface,  
    SetAssistantStatus,  
    ShowTextToScreen,  
    TempDirectoryPath,  
    SetMicrophoneStatus,  
    AnswerModifier,  
    QueryModifier,  
    GetMicrophoneStatus,  
    GetAssistantStatus  
)  
from Backend.Model import FirstLayerDMM  
from Backend.RealtimeSearchEngine import RealtimeSearchEngine  
from Backend.Automation import Automation  
from Backend.SpeechToText import SpeechRecognitionSystem as SpeechRecognition 
from Backend.Chatbot import ChatBot  
from Backend.TextToSpeech import TextToSpeech  
from dotenv import dotenv_values  
from asyncio import run  
from time import sleep  
import subprocess  
import threading  
import json  
import os  

env_vars = dotenv_values(".env")  
Username = env_vars.get("Username") or "Pranjal"
Assistantname = env_vars.get("Assistantname") or "Maverick"
DefaultMessage = f'''{Username} : Hello {Assistantname}, How are you?
{Assistantname} : Welcome {Username}. I am doing well. How may i help you?...'''  
subprocesses = []  
Functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]  

def ShowDefaultChatIfNoChats():
    File = open(r'Data\ChatLog.json', "r", encoding='utf-8')  
    if len(File.read()) < 5:  
        with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:  
            file.write("")
    
    with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as file:
        file.write(DefaultMessage)

def ReadChatLogJson():
    with open(r'Data\ChatLog.json', 'r', encoding='utf-8') as file:
        chatLog_data = json.load(file)
    return chatLog_data

def ChatLogIntegration():
    json_data = ReadChatLogJson()
    formatted_chatlog = ""
    for entry in json_data:
        if entry["role"] == "user":
            formatted_chatlog += f"User: {entry['content']}\n"
        elif entry["role"] == "assistant":
            formatted_chatlog += f"Assistant: {entry['content']}\n"
    formatted_chatlog = formatted_chatlog.replace("User", Username + " ")
    formatted_chatlog = formatted_chatlog.replace("Assistant", Assistantname + " ")
    
    with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
        file.write(AnswerModifier(formatted_chatlog))

def ShowChatsOnGUI():
    with open(TempDirectoryPath('Database.data'), "r", encoding='utf-8') as file:
        Data = file.read()
        if len(str(Data)) > 0:
            lines = Data.split('\n')
            result = '\n'.join(lines)
            with open(TempDirectoryPath('Responses.data'), "w", encoding='utf-8') as out_file:
                out_file.write(result)

def InitialExecution():
    SetMicrophoneStatus("False")
    ShowTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatsOnGUI()

InitialExecution()

def MainExecution():
    TaskExecution = False
    ImageExecution = False
    ImageGenerationQuery = ""

    SetAssistantStatus("Listening ...")
    Query = SpeechRecognition()
    ShowTextToScreen(f"{Username} : {Query}")
    SetAssistantStatus("Thinking ...")
    Decision = FirstLayerDMM(Query)
    
    print(f"\nDecision : {Decision}\n")
    
    G = any(i.startswith("general") for i in Decision)
    R = any(i.startswith("realtime") for i in Decision)
    Merged_query = " and ".join(
        " ".join(i.split()[1:]) for i in Decision 
        if i.startswith("general") or i.startswith("realtime")
    )
    
    for queries in Decision:
        if "generate " in queries:
            ImageGenerationQuery = str(queries)
            ImageExecution = True
            
    for queries in Decision:
        if not TaskExecution and any(queries.startswith(func) for func in Functions):
            run(Automation(list(Decision)))
            TaskExecution = True

    if ImageExecution:
        with open(r"Frontend\Files\ImageGeneration.data", "w") as file:
            file.write(f"{ImageGenerationQuery},True")
        try:
            p1 = subprocess.Popen(
                ['python', r'Backend\ImageGeneration.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                shell=False
            )
            subprocesses.append(p1)
        except Exception as e:
            print(f"Error starting ImageGeneration.py: {e}")

    if (G and R) or R:
        SetAssistantStatus("Searching ...")
        Answer = RealtimeSearchEngine(QueryModifier(Merged_query))
        ShowTextToScreen(f"{Assistantname}: {Answer}")
        SetAssistantStatus("Answering ...")
        TextToSpeech(Answer)
        return True
    
    else:
        for Queries in Decision:
            if "general" in Queries:
                SetAssistantStatus("Thinking ...")
                QueryFinal = Queries.replace("general ", "")
                Answer = ChatBot(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SetAssistantStatus("Answering ...")
                TextToSpeech(Answer)
                return True
                
            elif "realtime" in Queries:
                SetAssistantStatus("Searching ...")
                QueryFinal = Queries.replace("realtime ", "")
                Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SetAssistantStatus("Answering ...")
                TextToSpeech(Answer)
                return True
                
            elif "exit" in Queries:
                QueryFinal = "Okay, Bye!"
                Answer = ChatBot(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SetAssistantStatus("Answering ...")
                TextToSpeech(Answer)
                SetAssistantStatus("Answering ...")
                os._exit(1)  # Corrected from os_exit to os._exit

def FirstThread():
    while True:
        CurrentStatus = GetMicrophoneStatus()
        
        if CurrentStatus == "True":
            MainExecution()
        else:
            AIStatus = GetAssistantStatus()
            
            if "Available ..." in AIStatus:
                sleep(0.1)
            else:
                SetAssistantStatus("Available ...")

def SecondThread():
    GraphicalUserInterface()

if __name__ == "__main__":
    thread1 = threading.Thread(target=FirstThread, daemon=True)
    thread2 = threading.Thread(target=SecondThread, daemon=True)
    
    thread1.start()
    thread2.start()
    
    # Keep main thread alive while daemon threads run
    while True:
        sleep(1)                