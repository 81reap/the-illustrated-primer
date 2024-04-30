# Primer Frontend Components

This is the code for a React Native + Expo based inference UI. 

## Setup + Install

note :: this assumes server components are running and the frontend is correctly pointed at them

### Setting up and Interacting with the DB
```bash
## create the tables
curl -X POST -H "Content-Type: application/json" -d '{
  "statements": [
    "CREATE TABLE IF NOT EXISTS chats (timestamp TIMESTAMP, thread TEXT, role TEXT, message TEXT)"
  ]
}' http://100.94.67.41:8085
curl -X POST -H "Content-Type: application/json" -d '{
  "statements": [
    "CREATE TABLE IF NOT EXISTS threads (thread TEXT, title TEXT, summary TEXT, stale TIMESTAMP, saved BOOLEAN)"
  ]
}' http://100.94.67.41:8085

## empty the tables
curl -X POST -H "Content-Type: application/json" -d '{"statements": ["DELETE FROM chats;","DELETE FROM threads;"]}' http://100.94.67.41:8085

curl -X POST -H "Content-Type: application/json" -d '{"statements": ["DELETE FROM threads WHERE thread=\"thread_1714412362918\";"]}' http://100.94.67.41:8085

## check what's in the tables
curl -X POST -H "Content-Type: application/json" -d '{"statements": ["SELECT * FROM chats", "SELECT * FROM threads"]}' http://100.94.67.41:8085
```

### Setting up Expo Dev Apps

Install [Expo Go](https://expo.dev/go)

```bash
bun install
bun dev
```