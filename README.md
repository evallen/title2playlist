# Title2Playlist

Create a playlist from just a title!

```
>> eighties hits
0: Don't You (Forget About Me) by Simple Minds (from oldies)
1: Take On Me by a-ha (from PlayStation)
2: Africa by Toto (from 80's)
3: You Make My Dreams - Remastered by Daryl Hall & John Oates (from beach)
4: Wake Me up Before You Go-Go by Wham! (from 80's)
5: Everybody Wants To Rule The World by Tears For Fears (from before my time)
6: Jessie's Girl by Rick Springfield (from 🤤🤤)
7: Come On Eileen by Dexys Midnight Runners (from oldies)
8: Under Pressure - Remastered 2011 by Queen (from oldies)
9: I Wanna Dance with Somebody (Who Loves Me) by Whitney Houston (from 80's)
```

## Setup

1. Clone this repository.

2. Download and unzip the required playlist data to the `data/playlist/` folder 
   from [here](https://www.aicrowd.com/challenges/spotify-million-playlist-dataset-challenge). 

3. Install [Milvus, a vector-database](https://milvus.io/) and start running
   it locally.

4. Install the Python requirements:
   ```bash
   pip install -r requirements.txt
   ```

5. Create the Milvus playlist embedding dataset by running the following
   scripts (in this order):
   * `scripts/data_scripts/create_milvus_dataset.py`
   * `scripts/data_scripts/remove_test_split.ipynb` (this removes 1000 points
     to act as a test split)

6. Create the Playlist-Song dataset by running the following script:
   * `scripts/data_scripts/playlist_song_dataset.py`

7. Run the recommendation engine!
   ```
   python main.py
   ```
## Dataset files
The folder linked below contains all of the database and dataset files used during this project.

Link: [Folder Link](https://drive.google.com/drive/folders/1HyYqdHtue5exAiq7D0U9-RfV29Af1qI5?usp=share_link)

Original Dataset File:
 * `spotify_million_playlist_dataset.zip` - Contains the JSON slices for the original playlist dataset.
 
Database files from 1st attempt:
 * `song_dataset.db` - Contains music characteristic feature values for each individual song in the dataset.
 * `title_dataset.db` - Contains average and std deviation values formusic characteristic feature for each playlist in the datset.
 
Database files from 2nd attempt:
 * `playlist_song.db` - Contains playlists and their individual songs.
 
## Other files

This repository also contains some extra scripts from our previous
attempts in this project, including our old idea on representing
playlists as regions in song audio feature space.

The metrics in our paper can be found in `data/scripts/test_scripts/evaluate.ipynb`, and their implementations in `common/metrics.py`. 
