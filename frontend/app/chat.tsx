import React, { useState, useEffect } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, FlatList, View, Image, Pressable, StyleSheet, Modal, TouchableOpacity, TextInput } from "react-native";
import { Text } from '~/components/ui/text';
import { Input } from '~/components/ui/input';
import { Button } from '~/components/ui/button';
import { ThumbsUp, ThumbsDown, Copy, Plus, Send, Bot, User } from '~/components/Icons';
import { useTheme } from "@react-navigation/native";
import Markdown from "react-native-markdown-display";
//import AudioTranscriber from '~/components/core/AudioTranscriber';
import { useNavigation, useRouter, useLocalSearchParams } from "expo-router";


const sqldUrl = "http://100.94.67.41:8085";
const chatUrl = "http://100.94.67.41:8112/respond";

async function executeSql(statements: { q: string, params: any[] }[]) {
  const response = await fetch(sqldUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ statements })
  });
  if (!response.ok) {
    throw new Error(`HTTP error! Status: ${response.status}`);
  }
  return response.json();
}


export default function Chat() {
  const [history, setHistory] = useState([]);
  const [input, setInput] = useState("");
  const [transcript, setTranscript] = useState('');
  const [modalVisible, setModalVisible] = useState(false);

  const navigation = useNavigation();
  const router = useRouter();
  const params = useLocalSearchParams();
  const { thread } = params;

  const { colors } = useTheme();
  //const { startRecording, transcribeAudioFile } = AudioTranscriber();

  useEffect(() => {
    fetchChatHistory();
  }, []);

  async function fetchChatHistory() {
    try {
      const response = await executeSql([{ q: `SELECT * FROM chats WHERE thread = '${thread}'` }]);
      const chatsData = response[0].results;
      const columns = chatsData.columns;
      const rows = chatsData.rows;

      const formattedHistory = rows.map(row => {
        let chatObj = {};
        row.forEach((value, index) => {
          chatObj[columns[index]] = value;
        });
        return chatObj;
      });

      setHistory(formattedHistory);
    } catch (error) {
      console.error("Failed to fetch chat history:", error);
    }
  }

  const handleChat = async () => {
    try {
      const userTimestamp = Date.now()
      const processedHistory = history.map(item => ({
        content: item.message,
        role: item.role
      }));
      processedHistory.push({ content: input, role: "user" });
      console.log(processedHistory)
      
      const response = await fetch(chatUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          conversation: processedHistory
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();
      const assistantTimestamp = Date.now();

      console.log(data)

      await executeSql([
        { 
          q: "INSERT INTO chats (timestamp, thread, role, message) VALUES (?, ?, ?, ?)", 
          params: [userTimestamp, thread, 'user', input] 
        },
        { 
          q: "INSERT INTO chats (timestamp, thread, role, message) VALUES (?, ?, ?, ?)", 
          params: [assistantTimestamp, thread, 'assistant', data.response] 
        }
      ]);
      setInput(""); // This should reset the input field in your UI
      fetchChatHistory(); // This should update the chat history in your UI
    } catch (error) {
      console.error("Failed to create new chat:", error);
    }
};


  const handleRecordAudio = async () => {
    setModalVisible(false);
    //const transcription = await startRecording();
    setTranscript(transcription);
    console.log(transcription);
  };

  const handleUploadAudio = async () => {
    setModalVisible(false);
    //const transcription = await transcribeAudioFile();
    setTranscript(transcription);
    console.log(transcription);
  };

  return (
    <View className="flex-1">
      <ScrollView className="shrink">
        {history.map((message, index) => (
          <View key={index} className={message.role === "user" ? "bg-[--secondary] shrink" : "bg-[--background] shrink"}>
            <View className="mx-2 my-4 sm:mx-6 flex-row shrink">
              <MessageIcons role={message.role} />
              <Markdown style={styles(colors)}>{message.message}</Markdown>
            </View>
          </View>
        ))}
      </ScrollView>
      <View className="flex-row bg-[--background] border-t-4 border-[--border] mb-4">
        <Pressable className="m-2" onPress={() => setModalVisible(true)}>
          <Plus className='text-[--primary] shrink' size={35} strokeWidth={2} />
        </Pressable>
        <Input
          placeholder='Enter your prompt'
          value={input}
          onChangeText={setInput}
          aria-labelledby='inputLabel'
          aria-errormessage='inputError'
          className="h-fit w-full mt-2 flex-1"
        />
        <Pressable onPress={handleChat} className="m-2">
          <Send className='text-[--primary] shrink' size={35} strokeWidth={2} />
        </Pressable>
      </View>
      <Modal visible={modalVisible} animationType="slide" transparent={true}>
        <View className="flex-1 justify-center items-center bg-black bg-opacity-50">
          <View className="bg-white p-4 rounded-lg">
            <TouchableOpacity onPress={handleRecordAudio}>
              <Text>Record Audio</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={handleUploadAudio}>
              <Text>Upload Audio File</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => setModalVisible(false)}>
              <Text>Cancel</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
};

export const styles = (props: any) =>
  StyleSheet.create({
    body: {
      flex: 1,
    },
    text: {
      color: props.text,
    },
    table: {
      borderColor: props.primary,
    },
    tr: {
      borderColor: props.primary,
    },
    list_item: {
      color: props.text,
    }
  });

function MessageIcons({ role }) {
  if ("user" === role) {
    return (
      <View className="flex-col self-start m-2 w-10 sm:mr-4">
        <View className="bg-[--primary] rounded-full">
          <User className='text-[--primary-foreground] m-1 self-center' size={25} strokeWidth={2} />
        </View>
      </View>);
  };
  return (
    <View className="flex-col m-2 w-10 sm:mr-4">
      <View className="bg-[--accent] rounded-full">
        <Bot className='text-[--accent-foreground] m-1 self-center' size={25} strokeWidth={2} />
      </View>
      <Pressable className="selected:text-[--accent] m-2">
        <ThumbsUp className='text-[--primary]' size={25} strokeWidth={2} />
      </Pressable>
      <Pressable className="selected:text-accent m-2">
        <ThumbsDown className='text-[--primary]' size={25} strokeWidth={2} />
      </Pressable>
      <Pressable className="selected:text-accent m-2">
        <Copy className='text-[--primary]' size={25} strokeWidth={2} />
      </Pressable>
    </View>);
};