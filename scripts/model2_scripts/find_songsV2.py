#Imports all necessary dependencies
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sqlite3

def id_from_uri(uri: str):
    """Helper method to get the ID from a URI string like so:
    URI: 'spotify:artist:012345...'
    ID: '012345...'
    """
    return uri.split(':')[2]

def get_songs_from_playlist_slice(connection: sqlite3.Connection, playlistIDs):
    """Get the list of songs (IDs) from a list of playlist IDS.
    """
    songQuery = "SELECT songID FROM songs WHERE playlistID = ?"
    foundSongIDs = [] #List containing the songs found in the playlists
    for playlist in playlistIDs:
        songQuery = f"SELECT songID FROM songs WHERE playlistID = '{playlist}'"
        desiredSongIDs = pd.read_sql(songQuery, song_conn)
        [foundSongIDs.append(song) for song in desiredSongIDs.values.flatten().tolist()] #converts from pandas dataframe to a list
    return foundSongIDs
    
'''
#Code that uses JSON slices
      
#Intializes file name data variables
slice_lower = 0
slice_upper = 999
listOfSongIDs = list() #List that contains the list of song ids associated with the playlists
while(slice_upper <= 999999):
    fileName = f"../../data/playlist/mpd.slice.{slice_lower}-{slice_upper}.json" #Creates the file name for the json file we are analyzing
    #Opens the json file and load the slice into a data variable
    with open(fileName) as testSlice:
        slice_json = json.load(testSlice)
    listOfSongIDs.extend(get_songs_from_playlist_slice(slice_json, playListName="Top Hits")) #Gets list of Song IDs from the playlist
    slice_lower += 1000 #Increments lower bound of slice to update file name
    slice_upper += 1000 #Increments upper bound of slice to update the file name
print(len(listOfSongIDs))
'''


# %% [markdown]
# Now that we have obtained the list of Song IDS from the relevant playlist. We now create a ranked list with the top K song ID's relevant to the playlist. We will be ranking the list in terms of the songs appearance in these playlists.

# %%
def generate_songs(playlist_ids, num):
    ''' Generate <num> songs from a list of playlist IDs '''
    all_songs = get_songs_from_playlist_slice(song_conn, playlist_ids)
    songDict = {}
    for songID in all_songs:
        if songID in songDict.keys():
            songDict[songID] = songDict[songID] + 1 #increments the song ID occurence counter by 1 if the song id has been found
        else:
            songDict[songID] = 1 #Intializes the new key and value for the new song id.
    #Gets the contents of the dictionary and formulates it into a list of tuples.
    rankedsongsList = list(songDict.items())
    #Sorts the song id list by the most occurences to the least amount of occurences.
    rankedsongsList = sorted(rankedsongsList, key=lambda occurence: occurence[1], reverse=True)
    # print(rankedsongsList)
    # Top 10 songs
    for i in range(num):
        songQuery = f"SELECT * FROM songs WHERE songID = '{rankedsongsList[i][0]}' LIMIT 1"
        topSongs = pd.read_sql(songQuery, song_conn)
        print(f"{i}: {topSongs['songName'].values.squeeze()} by {topSongs['artistName'].values.squeeze()}")
    # print(topSongs['songID'].values)
    
#Code that uses playlist_song.db
#Forms a connection with the database
song_conn = sqlite3.Connection("../../data/playlist_song.db")
songCur = song_conn.cursor()
#Query for getting playlist IDs TO BE REMOVED
playlistQuery = "SELECT playlistID FROM songs WHERE LOWER(playlistName) = LOWER('Top Hits')"
#Gets desired playlist ID's list
desiredPlaylistsID = pd.read_sql(playlistQuery,song_conn)
desiredPlaylistsID = desiredPlaylistsID.values.flatten().tolist() #converts from pandas dataframe to a list
desiredPlaylistsID = list(set(desiredPlaylistsID)) #Gets rid of repeated values
listOfSongIDs = get_songs_from_playlist_slice(song_conn, desiredPlaylistsID) # Retrieves a list of song ID's from the given playlist IDs
# listOfSongIDs.extend(listOfSongIDs)
# print(len(listOfSongIDs))

generate_songs(desiredPlaylistsID, 10)


