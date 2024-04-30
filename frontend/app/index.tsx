import React, { useState, useEffect } from "react";
import { View, Pressable, ScrollView, Modal, TouchableOpacity } from "react-native";
import { Text } from '~/components/ui/text';
import { Input } from '~/components/ui/input';
import { Button } from '~/components/ui/button';
import { Plus, Bookmark } from '~/components/Icons';
import Countdown from "~/components/Countdown";
import { useNavigation } from "@react-navigation/native";
import { Link } from 'expo-router';

const sqldUrl = "http://100.94.67.41:8085";

async function executeSql(statements) {
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

export default function Threads() {
  const [threads, setThreads] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [threadTitle, setThreadTitle] = useState("");
  const navigation = useNavigation();

  useEffect(() => {
    fetchThreads();
  }, []);

  const createNewChat = () => {
    setModalVisible(true);
  };

  const fetchThreads = async () => {
    try {
      const response = await executeSql([{ q: "SELECT * FROM threads" }]);
      const { columns, rows } = response[0].results;
      const formattedThreads = rows.map(row => {
        const threadObj = {};
        row.forEach((value, index) => {
          threadObj[columns[index]] = value;
        });
        return threadObj;
      });
      // Sort threads such that bookmarked (saved) threads come first
      formattedThreads.sort((a, b) => b.saved - a.saved);
      setThreads(formattedThreads);
    } catch (error) {
      console.error("Failed to fetch threads:", error);
    }
  };

  const confirmThreadTitle = async () => {
    try {
      await executeSql([
        `INSERT INTO threads (thread, title, summary, stale, saved)
         VALUES ('thread_${Date.now()}', '${threadTitle}', 'New chat summary', ${Date.now() + 24*60*60*1000}, false)`
      ]);
      fetchThreads();
      setModalVisible(false);
      setThreadTitle("");
    } catch (error) {
      console.error("Failed to create new chat:", error);
    }
  };

  const toggleSaveThread = async (thread) => {
    try {
      await executeSql([
        `UPDATE threads SET saved = ${!thread.saved} WHERE thread = '${thread.thread}'`
      ]);
      fetchThreads();
    } catch (error) {
      console.error("Failed to save/unsave thread:", error);
    }
  };

  return (
    <View className="flex-1 bg-[--primary]">
      <ScrollView>
        {threads.map((thread, index) => (
          <View key={index} className="flex-row rounded-lg mx-2 mt-2 bg-[--card] border-[--border] shadow">
            <Link push href={{ pathname: "/chat", params: { thread: thread.thread }}} asChild>
              <Pressable className="m-2 flex-1 flex-col">
                <Text className="font-black text-[--card-foreground] shrink">{thread.title}</Text>
                <Text className="text-[--card-foreground] shrink">{thread.summary}</Text>
                <Countdown className="text-[--accent]" targetDate={thread.stale} />
              </Pressable>
            </Link>
            <Pressable onPress={() => toggleSaveThread(thread)} className="m-2 self-center shrink">
              <Bookmark className={`${thread.saved ? 'fill-green-600' : ''} text-[--ring]`} size={25} strokeWidth={2} />
            </Pressable>
          </View>
        ))}
      </ScrollView>
      <Pressable
        onPress={createNewChat}
        className="absolute bottom-4 right-4 bg-[--accent] rounded-full p-4"
      >
        <Plus className="text-[--accent-foreground]" size={25} strokeWidth={2} />
      </Pressable>
      <Modal visible={modalVisible} animationType="slide" transparent={true}>
        <View className="flex-1 justify-center items-center bg-black/75">
          <View className="flex-col bg-[--card] p-4 rounded-lg">
            <Input
              placeholder="Enter thread title"
              value={threadTitle}
              onChangeText={setThreadTitle}
              className="p-2 mb-4 bg-[--input]"
            />
            <View className="flex-row">
              <Button onPress={() => setModalVisible(false)} className="mr-2">
                <Text>Cancel</Text>
              </Button>
              <Button onPress={confirmThreadTitle} className="ml-2">
                <Text>Confirm</Text>
              </Button>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}