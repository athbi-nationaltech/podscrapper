import argparse
import json
import os
from pprint import pprint
import requests
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tqdm import tqdm
from youtube_transcript_api import YouTubeTranscriptApi


load_dotenv()
api_key = os.getenv("YTB_API_KEY")
youtube = build("youtube", "v3", developerKey=api_key)


def get_channel_id(channel_name):
    """
    Retrieves the id of a youtube channel from its channel name.

    Args:
      channel_name: Name of the youtube channel which is not the full name of channel but the name after the '@'
                    the channel link.

    Returns:
      The id of of the given channel.
    """
    url = "https://www.youtube.com/@" + channel_name
    r = requests.get(url)
    # Retrieve the whole page source
    text = r.text
    # Split the text to get only the section containing the channel id
    id = text.split("youtube.com/channel/")[1].split('">')[0]
    return id


def fetch_video_ids(channel_name):
    """
    Fetches the video IDs of the videos in the uploads playlist of a channel.
    Args:
      channel_name: The name of the channel.
    Returns:
      A list of {video ID, video url, title}.
    """
    # Make a request to youtube api
    base_url = "https://www.googleapis.com/youtube/v3/channels"
    channel_id = get_channel_id(channel_name)
    # print(channel_id)
    params = {"part": "contentDetails", "id": channel_id, "key": api_key}
    # print(params)
    try:
        response1 = requests.get(base_url, params=params)
        response = json.loads(response1.content)
        # print(response)
        # raise Exception(f"No playlist found for {channel_name}")
        
    except HttpError as e:
        print(f"An HTTP error occurred: {e}")
        return []
    # print(response1)
    if "items" not in response or not response["items"]:
        raise Exception(f"No playlist found for {channel_name}")

    # Retrieve the uploads playlist ID for the given channel
    playlist_id = response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    # Retrieve all videos from uploads playlist
    videos = []
    next_page_token = None

    while True:
        playlist_items_response = (
            youtube.playlistItems()
            .list(
                # part="contentDetails",
                part="snippet, contentDetails, status, id",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token,
            )
            .execute()
        )

        videos += playlist_items_response["items"]

        next_page_token = playlist_items_response.get("nextPageToken")

        if not next_page_token:
            break

    # Extract video URLs
    video_urls = []
    

    for video in videos:
        video_id = video["snippet"]["resourceId"]["videoId"]
        publishedAt = video["snippet"]["publishedAt"]
        channelTitle = video["snippet"]["channelTitle"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        video_title = video["snippet"]["title"]
        video_urls.append({"ID": video_id, "URL": video_url, "Title": video_title, "publishedAt": publishedAt, "channelTitle": channelTitle})
        
    # for video in videos:
    #     pprint(video)
    #     pprint("------")
    return video_urls


def fetch_and_save_transcript(video_id, file_name, file_name2):
    """
    Saves the transcript of a video in a file.
    Args:
      transcript: The transcript of the video.
      file_name: The name of the file in which the transcript will be saved.
    Returns:
        True if the transcript was saved successfully, False otherwise.
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["ar"])
        # print(transcript)
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    # with open(file_name, "w", encoding="utf-8") as file:
    with open(file_name, "w", encoding='utf8') as file:
        json.dump(transcript, file,indent=4,ensure_ascii=False)

    with open(file_name2, "w", encoding="utf-8") as file:
        for line in transcript:
            file.write(line["text"] + "\n")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--channel_name", help="The name of the channel.", type=str)
    parser.add_argument(
        "--results_dir",
        help="The directory to save the transcripts.",
        type=str,
        default="transcripts",
    )
    parser.add_argument(
        "--max_videos",
        help="The max number of transcripts.",
        type=int,
        default=None,
    )

    args = parser.parse_args()
    max_videos = args.max_videos
    channel_name = args.channel_name
    results_dir = args.results_dir

    TRANSCRIPTS_DIR = os.path.join(os.getcwd(), channel_name)
    TRANSCRIPTS_DIRTEXT = TRANSCRIPTS_DIR + "/raw"
    TRANSCRIPTS_DIRJson =TRANSCRIPTS_DIR + "/json"
    os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
    os.makedirs(TRANSCRIPTS_DIRTEXT, exist_ok=True)
    os.makedirs(TRANSCRIPTS_DIRJson, exist_ok=True)
    # break

    print(f"Fetching video IDs for {channel_name}...")
    videos = fetch_video_ids(channel_name)
    # print(videos)
    # print("videos:", type(videos))
    if max_videos:
        videos = videos[:max_videos]

    print(f"Fetching transcripts for {channel_name}...")
    cnt = 0
    for i, video in enumerate(tqdm(videos)):
        video_id = video["ID"]
        output_file = os.path.join(TRANSCRIPTS_DIR,"json", f"{results_dir}_{i}_{video_id}.json")
        output_file2 = os.path.join(TRANSCRIPTS_DIR,"raw", f"{results_dir}_{i}_{video_id}.txt")
        json_file = os.path.join(TRANSCRIPTS_DIR, "transcripts.json")
        # pprint(video)
        # print("====")
        # save transcript
        success = fetch_and_save_transcript(video["ID"], output_file, output_file2 )

        # save json file with transcript_path, video_url, video_title
        if success:
            with open(json_file, "a", encoding="utf-8", newline="\n") as file:
                json.dump(
                    {
                        "status": "success" if success else "failed",
                        "channel_name": channel_name,
                        "transcript_path": output_file if success else "",
                        "video_url": video["URL"],
                        "video_title": video["Title"],
                    },
                    file,
                    ensure_ascii=False,
                    indent=4,
                )
            cnt += 1

    print(f"Saved {cnt} transcripts for {channel_name}.")
