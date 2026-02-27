# Trivia Engine

A Tkinter-based desktop application designed to manage a master trivia database and automatically generate randomized Jeopardy-style game boards. I wanted to play some jeopardy games with my friends but finding and adding questions was hard so I made this. Works in tangent with my other repository (jeopardy-Player) to play the game. 

## How It Works

The application stores all data locally in `master_trivia_database.json` and operates across four main tabs:

* **Add Question:** Manually enter new trivia clues. You can set the category, difficulty level (100–1000 points), and media type (text, image, YouTube, or Spotify). You can also include media URLs and optional host notes.
* **Import Data:** Perform smart batch imports using JeopardyLabs HTML files or JSON exports. The tool parses the file and provides a UI to map imported categories to your existing database. It also includes an option to standardize imported point values to a standard 100–500 scale.
* **Manage Categories:** Consolidate your database by transferring all questions from a source category into a destination category. The app automatically deletes the source category once the transfer is complete.
* **Generate Game:** Scans the master database for categories that contain a complete point spread (at least one question for 100, 200, 300, 400, and 500 points). It then randomly selects 5 valid categories, picks random questions for each slot, and outputs a ready-to-play `game.json` file.

## Requirements

This application relies entirely on Python's standard library. No external dependencies are required.

* Python 3.x
* `tkinter` (Usually bundled with Python)

## Usage

Run the script from your terminal to launch the GUI:

```bash
python trivia_engine.py
```

## Data Structures

The application uses two distinct JSON structures for the master database and the generated game boards.

### Master Database (`master_trivia_database.json`)
This file stores all your curated categories and questions.

```json
{
  "databaseTitle": "Ultimate Master Anime Trivia Database",
  "categories": [
    {
      "name": "Studio Ghibli",
      "clues": [
        {
          "difficulty": 100,
          "type": "text",
          "prompt": "What is the name of the giant cat-like spirit in Hayao Miyazaki's 1988 film?",
          "response": "Totoro",
          "url": "",
          "hostNotes": "Accept 'My Neighbor Totoro'"
        }
      ]
    }
  ]
}