###    Fichier "Mp3Land.py" créé par Julien Noel (MAM3 PNS)    ###
###    Dernière mise à jour :           21/04/2025             ###



#===========================[ Imports ]===========================

from copy import copy
#from eyed3 import load
from numpy import maximum
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
from os import listdir, startfile
from os.path import dirname, exists, isdir, join, realpath
from random import choice, randrange
import subprocess
from tkinter import *
from tkinter.ttk import *
import time
from typing import List, Tuple, Union
from vlc import Instance
import xml.etree.ElementTree as ET

#=================================================================



#=====================[ Variables globales ]======================

currentDirectoryPath = str(dirname(realpath(__file__))).replace("\\", "/")
musicFolder = "C:/Juju/Musique"

#=================================================================



#===========================[ Classes ]===========================

# Classe pour les chansons
class Song(object) :

    def __init__(self, path:str="", title:str="", subtitle:str="", comment:str="", artists:List[str]=[], duration:int=0, year:int=0, album:str="", order:int=0) -> None :
        if exists(path) and path.endswith(".mp3") :
            audioFile = MP3(path, ID3=ID3)
            tag = audioFile.tags
            title = tag.get('TIT2').text[0] if "TIT2" in tag else ""
            subtitle = tag.get("TIT3").text[0] if "TIT3" in tag else ""
            comment = tag.get("COMM::fra").text[0] if tag.get("COMM::fra") else ""
            artists = sorted(tag.get("TPE1").text[0].split("/")) if "TPE1" in tag else []
            album = tag.get("TALB").text[0] if "TALB" in tag else ""
            order = int(tag.get("TRCK").text[0]) if "TRCK" in tag and tag.get("TRCK").text[0].isdigit() else 0
            year = int(str(tag.get("TDRC").text[0])[:4]) if "TDRC" in tag else 0
            duration = round(audioFile.info.length)
        else :
            path = ""
        self.path = str(path)
        self.title = str(title)
        self.subtitle = str(subtitle)
        self.comment = str(comment)
        self.artists = list(artists)
        self.duration = max(duration, 0)
        self.year = max(year, 0)
        self.album = str(album)
        self.order = max(order, 0)
        
    def __eq__(self, other:"Song") -> bool :
        return isinstance(other, Song)                                          \
                and self.path == other.path                                     \
                and self.title == other.title                                   \
                and self.subtitle == other.subtitle                             \
                and self.comment == other.comment                               \
                and all(a == o for a, o in zip(self.artists, other.artists))    \
                and self.duration == other.duration                             \
                and self.year == other.year                                     \
                and self.album == other.album                                   \
                and self.order == other.order
    
    def plural(n:int) -> str :
        return ("s" if abs(n) > 1 else "")

    def __str__(self) -> str :
        return ("        Titre:  " + self.title + (" " + self.subtitle if self.subtitle != "" else "") if self.title != "" else "")                                                                                                                                    \
                + ("\n     " + ("" if len(self.artists) > 1 else " ") + "Artiste" + Song.plural(len(self.artists)) + ":  " + ", ".join(self.artists) if not(not(self.artists)) else "")                                                                                \
                + ("\n        Durée:  " + (str(self.duration // 60) + " minute" + Song.plural(self.duration // 60) + " et " if self.duration // 60 > 0 else "") + str(self.duration % 60) + " seconde" + Song.plural(self.duration % 60) if self.duration > 0 else "") \
                + ("\n        Année:  " + str(self.year) if self.year != 0 else "")                                                                                                                                                                                    \
                + ("\n        Album:  " + self.album + " [n°" + str(self.order) + "]" if self.album != "" and self.order > 0 else "")                                                                                                                                  \
                + ("\n  Commentaire:  " + self.comment if self.comment != "" else "")

    def writtenBy(self, a:str) -> bool :
        return (a in self.artists)
    
    def writtenBy(self, l:List[str]) -> List[bool] :
        return [self.writtenBy(a) for a in l]

    def fromAll(self, l:List[str]) -> bool :
        for a in l :
            if not(self.writtenBy(a)) :
                return False
        return True

    def fromOne(self, l:List[str]) -> bool :
        for a in l :
            if self.writtenBy(a) :
                return True
        return False
    
    def isNull(self) :
        return self.path == ""          \
                and self.title == ""    \
                and self.subtitle == "" \
                and self.comment == ""  \
                and not(self.artists)   \
                and self.duration == 0  \
                and self.year == 0      \
                and self.album == ""    \
                and self.order == 0


# Classe pour les playlists de chansons
class Playlist(object) :

    def __init__(self, songs:Union[List[str],"Playlist"]=[], folders:List[str]=[], name:str="") -> None :
        if isinstance(songs, Playlist) :
            songs = songs.songs
        for folder in folders :
            if isdir(folder) :
                files = listdir(folder)
                for file in files :
                    if file.endswith(".mp3") :
                        folder += "/" if not(folder.endswith("/")) else ""
                        song = Song(folder + file)
                        if all(song != s for s in songs) :
                            songs.append(song)
        songsBis = []
        for s in songs :
            if isinstance(s, Song) and not(s.isNull()) :
                songsBis.append(s)
            elif isinstance(s, str) and exists(s) and s.endswith(".mp3") :
                songsBis.append(Song(s))
        self.songs = list(songsBis)
        self.name = str(name)

    def __add__(self, other:Union[Song,"Playlist"]) -> "Playlist" :
        songs = copy(self.songs)
        if isinstance(other, Song) and not(other.isNull()) :
            songs.append(other)
        elif isinstance(other, "Playlist") :
            songs = songs + other
        return Playlist(songs)

    def __radd__(self, other:Song) -> "Playlist" :
        songs = copy(self.songs)
        if isinstance(other, Song) and not(other.isNull()) :
            songs.insert(0, other)
        return Playlist(songs)

    def __str__(self) -> str :
        s = "\n\n### Voici " + ("la playlist \"" + self.name + "\"" if self.name != "" else "une playlist") + " ###\n\n"
        for song in self.songs :
            s += "Chanson n°" + str(self.songs.index(song)+1) + " :\n" + str(song) + "\n\n"
        return s

    def __len__(self) -> int :
        return len(self.songs)
    
    def __iter__(self) -> iter :
        return iter(self.songs)
    
    def __eq__(self, other:"Playlist") -> bool :
        return isinstance(other, Playlist)                                      \
                and self.name == other.name                                     \
                and all(s == o for s, o in zip(self.songs, other.songs))
    
    def __gt__(self, other:"Playlist") -> bool :
        return isinstance(other, Playlist) and len(self) > len(other)
    
    def __lt__(self, other:"Playlist") -> bool :
        return other > self
    
    def __ge__(self, other:"Playlist") -> bool :
        return self > other or len(self) == len(other)
    
    def __le__(self, other:"Playlist") -> bool :
        return other >= self

    def getSong(self, i:int=0) -> Song :
        return self.songs[i]

    def getAllArtists(self) -> List[str] :
        l = []
        for s in self.songs :
            for a in s.artists :
                if a not in l :
                    l.append(a)
        return l

    def allWrittenBy(self, a:str) -> bool :
        for s in self.songs :
            if not(s.writtenBy(a)) :
                return False
        return True

    def sorting(self, option:str="", ascending:bool=True) -> None :
        if option not in ["song-name", "song-year", "song-album", "song-duration", "song-path"] :
            option = "song-name"
        def choosen(s:Song) -> str :
            if option == "song-name" :
                return s.title + " " + s.subtitle
            if option == "song-year" :
                return str(s.year)
            if option == "song-album" :
                return s.album
            if option == "song-duration" :
                return str(s.duration)
            if option == "song-path" :
                return s.path
            return ""
        if option != "song-album" :
            def order(s:Song) -> Tuple[bool,str] :
                return ((choosen(s)==""), choosen(s))
            self.songs = sorted(self.songs, key=order, reverse=not(ascending))
        else :
            def albumOrder(s:Song) -> Tuple[bool,str,bool,int] :
                if s.album == "" :
                    return (True, s.title, True, 0)
                return (False, s.album, (s.order==0), s.order)
            self.songs = sorted(self.songs, key=albumOrder, reverse=False)

    def recentYear(self) -> int :
        return max([s.year for s in self.songs]) if not(not(self.songs)) else 0
    
    def isNull(self) -> bool :
        return not(self.songs) and self.name == ""


# Classe pour des playlists particulières
class Album(Playlist) :

    def __init__(self, songs:List[str]=[], folders:List[str]=[], name:str="", artist:str="", year:int=0) -> None :
        Playlist.__init__(self, songs=songs, folders=folders, name=name)
        r = []
        for s in self.songs :
            if (s.album == "") or (s.album != name) or (artist not in s.artists) :
                r.append(s)
        self.songs = list([s for s in self.songs if s not in r])
        Playlist.sorting(self, "song-album")
        self.artist = str(artist)
        if year == 0 :
            year = Playlist.recentYear(self)
        self.year = int(year)

    def __str__(self) :
        s = "\n\n### Voici " + ("l'album \"" + self.name + "\"" if self.name != "" else "un album") + " ###\n"  \
            + ("\n  Artiste: " + self.artist if self.artist != "" else "")                                        \
            + ("\n    Année: " + str(self.year) if self.year != 0 else "")                                        \
            + "\n\n"
        for song in self.songs :
            ats = copy(song.artists)
            ats.remove(self.artist)
            s += "Titre n°" + str(song.order) + " :"                                                                                                                                                                                                                    \
                + ("\n          Nom:  " + song.title + (" " + song.subtitle if song.subtitle != "" else "") if song.title != "" else "")                                                                                                                                   \
                + ("\n    Featuring:  " + ", ".join(ats) if not(not(ats)) else "")                                                                                                                                                                                         \
                + ("\n        Durée:  " + (str(song.duration // 60) + " minute" + Song.plural(song.duration // 60) + " et " if song.duration // 60 > 0 else "") + str(song.duration % 60) + " seconde" + Song.plural(song.duration % 60) if song.duration > 0 else "")     \
                + ("\n  Commentaire:  " + song.comment if song.comment != "" else "")                                                                                                                                                                                   \
                + "\n\n"
        return s
    
    def __eq__(self, other:"Album") :
        return Playlist.__eq__(self, other)         \
                and isinstance(other, Album)        \
                and self.artist == other.artist     \
                and self.year == other.year


# Classe pour créer un lecteur de musique
class MusicPlayer(object) :
    
    def __init__(self, playlist:Union[Playlist,List[str]]=Playlist(), randomPlay:bool=True, autoPlay:bool=False, printPlayer:bool=True) -> None :
        if isinstance(playlist, list) and all(isinstance(s, str) for s in playlist) :
            playlist = Playlist(songs=playlist)
        if len(playlist) == 0 :
            raise ValueError("Votre playlist doit contenir au moins une chanson !")
        self.instance = Instance()
        self.playlist = playlist
        self.randomPlay = randomPlay
        self.autoPlay = autoPlay
        self.songsAlreadyPlayed = []
        self.songsToPlay = copy(self.playlist.songs)
        self.currentOriginalPlaylistIndex = randrange(len(self.playlist)) if self.randomPlay else 0
        self.songCurrentlyPlaying = self.playlist.songs[self.currentOriginalPlaylistIndex]
        self.songsToPlay.pop(self.currentOriginalPlaylistIndex)
        self.mediaList = self.instance.media_list_new()
        self.mediaListPlayer = self.instance.media_list_player_new()
        self.mediaListPlayer.set_media_list(self.mediaList)
        self.mediaList.add_media(self.instance.media_new(self.songCurrentlyPlaying.path))
        self.mediaPlayer = self.mediaListPlayer.get_media_player()
        self.playlistProgression = 1
        self.playlistIndexes = [self.currentOriginalPlaylistIndex]
        # if printPlayer :
        #     subprocess.Popen(["vlc", "-I", "qt"])
        if self.autoPlay :
            self.play()
    
    def setAutoPlay(self, auto:bool=True) -> None :
        self.autoPlay = auto
    
    def changeAutoPlay(self) -> None :
        self.setAutoPlay(not(self.autoPlay))
        
    def checkSongEnd(self) -> None :
        # while not(self.stopThread) :
        #     if self.mediaListPlayer.get_state() == State.Ended :
        #         self.next()
        #         if self.autoPlay :
        #             self.stopThread = True
        #             self.play()
        pass
    
    def checkPlay(self) -> None :
        # while not(self.stopThread) :
        #     if self.changeAutoPlay() and self.autoPlay :
        #         self.stopThread = True
        #         self.play()
        pass
    
    def setTime(self, t:int) -> None :
        self.mediaPlayer.set_time(t)
        
    def resetTime(self) -> None :
        self.setTime(0)
        
    def getTime(self) -> int :
        return self.mediaPlayer.get_time()
    
    def play(self) -> None :
        self.mediaListPlayer.play()
    
    def pause(self) -> None :
        self.mediaListPlayer.pause()
        
    def replay(self) -> None :
        self.pause()
        self.resetTime()
        self.play()

    def stop(self) -> None :
        self.mediaListPlayer.stop()

    def next(self) -> None :
        self.songsAlreadyPlayed.append(self.songCurrentlyPlaying)
        if len(self.songsAlreadyPlayed) == len(self.playlist) :
            self.songsAlreadyPlayed = []
            self.songsToPlay = copy(self.playlist.songs)
        if self.randomPlay :
            self.songCurrentlyPlaying = choice(self.songsToPlay)
            for index, song in enumerate(self.playlist) :
                if song == self.songCurrentlyPlaying :
                    self.currentOriginalPlaylistIndex = index
                    break
        else :
            self.currentOriginalPlaylistIndex = (self.currentOriginalPlaylistIndex + 1) % len(self.playlist)
            self.songCurrentlyPlaying = self.playlist.getSong(self.currentOriginalPlaylistIndex)
        for index, song in enumerate(self.songsToPlay) :
            if song == self.songCurrentlyPlaying :
                self.songsToPlay.pop(index)
                break
        self.mediaList.add_media(self.instance.media_new(self.songCurrentlyPlaying.path))
        self.playlistIndexes.append(self.currentOriginalPlaylistIndex)
        self.playlistProgression += 1
        self.mediaListPlayer.next()

    def previous(self) -> None :
        if (self.playlistProgression == 1) :
            self.replay()
        else :
            self.songsToPlay.append(self.songCurrentlyPlaying)
            if len(self.songsToPlay) == len(self.playlist) :
                self.songsAlreadyPlayed = copy(self.playlist.songs)
                self.songsToPlay = []
            if self.randomPlay :
                self.songCurrentlyPlaying = self.songsAlreadyPlayed[-1]
                for index, song in enumerate(self.playlist) :
                    if song == self.songCurrentlyPlaying :
                        self.currentOriginalPlaylistIndex = index
                        break
            else :
                self.currentOriginalPlaylistIndex = (self.currentOriginalPlaylistIndex - 1) % len(self.playlist)
                self.songCurrentlyPlaying = self.playlist.getSong(self.currentOriginalPlaylistIndex)
            for index, song in enumerate(self.songsAlreadyPlayed) :
                if song == self.songCurrentlyPlaying :
                    self.songsAlreadyPlayed.pop(index)
                    break
            self.playlistIndexes.append(self.currentOriginalPlaylistIndex)
            self.mediaListPlayer.previous()
            self.playlistProgression -= 1
            self.mediaList.remove_media(self.playlistProgression)
            

#==========================[ Fonctions ]==========================

# Fonction qui permet d'avoir le chemin absolu d'un dossier et/ou d'une chanson
def wholePath(path:str, folder:str=musicFolder) -> str :
    return folder + "/" + path


# Fonction permettant d'avoir tous les dossiers d'album
def allAlbumPaths(folder:str=musicFolder) -> List[str] :
    return [wholePath(d, folder) for d in listdir(folder) if isdir(join(folder, d)) and d != "Autre"]


# Fonction pour obtenir toutes les chansons d'un dossier et les mettre dans une playlist
def allSongs(folder:str=musicFolder, name:str="") -> Playlist :
    d = allAlbumPaths(folder)
    d.append(folder)
    p = Playlist(folders=d, name=name)
    p.sorting(option="song-album")
    return p


# Fonction
def createPlaylist(name:str="Everything ma gueule", path=currentDirectoryPath+"/List of songs.txt") -> Playlist :
    p = allSongs(name=name)
    with open(path, "w") as f :
        f.write(str(p))
        f.close()
    startfile(path)
    return p

#=================================================================



#=====================[ Fonction principale ]=====================

def main(test=False) :
    if __name__ == "__main__" :
        playlist = createPlaylist()
        if test :
            songs = [Song(wholePath("Calvin Harris - My way.mp3")), Song(wholePath("Alok and Bhaskar - Fuego.mp3"))]
            folders = [wholePath("Rare (by Selena Gomez)"), wholePath("Random Access Memories (by Daft Punk)")]
            playlistBis = Playlist(songs=songs, folders=folders)
            playlistBis.sorting(option="song-album")
            print(playlistBis)
            album = Album(playlist, name="Random Access Memories", artist="Daft Punk")
            print(album)
            albumBis = Album(playlist, name="Hey U X", artist="Benee")
            print(albumBis)
            # player = MusicPlayer(playlist=playlist, autoPlay=True)
            player = MusicPlayer(playlist=Album(playlist,name="Random Access Memories",artist="Daft Punk"), autoPlay=True)
            for i in range(15) :
                time.sleep(1)
                player.next()
                time.sleep(1)
                player.replay()
                player.stop()


main(True)

#=================================================================


# for the future:   https://stackoverflow.com/questions/28440708/python-vlc-binding-playing-a-playlist
#                   https://stackoverflow.com/questions/60250171/how-to-play-random-mp3-files-in-pygame
