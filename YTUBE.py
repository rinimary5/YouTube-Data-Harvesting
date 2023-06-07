from googleapiclient.discovery import build
import pymongo as pym
import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space
import pandas as pd
import re
import altair as alt
import isodate
import math
import mysql.connector
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import plotly.express as px
st.set_page_config(layout='wide')

# Title
st.title(':blue[Youtube Data Harvesting and Warehousing]')
col1, col2 = st.columns(2)
#Data Harvesting column
with col1:
    st.header(':red[Data Harvesting]')
    channel_id = st.text_input('Enter Channel Id')
    data_butt = st.button('Get data and store')

    if data_butt:
        st.session_state.Get_state = True
        youtube = build('youtube', 'v3',
                        developerKey='AIzaSyDw1YRbRin980ol1sUQD4JrSNSdfnZep8Q')

#TO GET CHANNEL DATA
        def get_channel_data(youtube, channel_id):
            ch_request = youtube.channels().list(
                part='statistics,snippet',
                id=channel_id)

            channel_response = ch_request.execute()
            return channel_response

#TO GET PLAYLIST DATA
        def get_playlist_data(youtube, channel_id):
            request = youtube.playlists().list(
                part="snippet",
                channelId=channel_id,
                maxResults=50
            )
            response = request.execute()
            playlists = []
            while request is not None:
                response = request.execute()
                playlists += response["items"]
                request = youtube.playlists().list_next(request, response)
            playlist_id = []
            playlist_title = []
            for i in playlists:
                playlist_id.append(i['id'])
                playlist_title.append(i['snippet']['localized']['title'])
            return playlist_id, playlist_title


        playlist_id, playlist_title = get_playlist_data(youtube, channel_id)

#TO GET VIDEO ID'S
        def get_video_ids(youtube, playlistId):
            nextPageToken = None
            pl_request = youtube.playlistItems().list(
                part='snippet',
                playlistId=playlistId,
                maxResults=50,
                pageToken=nextPageToken
            )
            pl_response = pl_request.execute()
            return pl_response

#TO GET VIDEO DATA
        def get_video_data(youtube, video_idn):
            video_request = youtube.videos().list(
                part='snippet,contentDetails,statistics',
                id=video_idn
            )
            video_response = video_request.execute()
            return video_response

#TO GET COMMENT DETAILS
        def get_video_comments(youtube, video_idn):
            comments_response = youtube.commentThreads().list(
                part='id,snippet,replies',
                videoId=video_idn
            ).execute()
            return comments_response

#FOR CONVERTING DURATION
        def conv_duration(duration):
            regex = r'PT(\d+H)?(\d+M)?(\d+S)?'
            match = re.match(regex, duration)
            if not match:
                return '00:00:00'
            hours, minutes, seconds = match.groups()
            hours = int(hours[:-1]) if hours else 0
            minutes = int(minutes[:-1]) if minutes else 0
            seconds = int(seconds[:-1]) if seconds else 0
            total_seconds = hours * 3600 + minutes * 60 + seconds
            return '{:02d}:{:02d}:{:02d}'.format(int(total_seconds / 3600), int((total_seconds % 3600) / 60),
                                                 int(total_seconds % 60))


        playlist_id, playlist_title = get_playlist_data(youtube, channel_id)
        video_id = {}
        video_id1 = []
        v_description = {}
        v_name = []
        v_name1 = {}
        d = {}
        #FOR LOOPING THROUGH ALL PLAYLIST ID'S
        for i in playlist_id:
            # print(i)
            v_description[i] = {}
            d[i] = {}
            vid = []
            vna = []
            playlistId = i
            nextPageToken = None
            while True:
                pl_response = get_video_ids(youtube, playlistId)
                for item in pl_response['items']:
                    d[i][item['snippet']['resourceId']['videoId']] = {}
                    d[i][item['snippet']['resourceId']['videoId']]['published'] = item['snippet']['publishedAt']
                    vid.append(item['snippet']['resourceId']['videoId'])
                    v_description[i][item['snippet']['resourceId']['videoId']] = item['snippet']['description']
                    v_name1[item['snippet']['resourceId']['videoId']] = item['snippet']['title']
                video_id[i] = vid
                video_id1.append(vid)
                nextPageToken = pl_response.get('nextPageToken')
                if not nextPageToken:
                    break
#DELETING PLAYLISTS THAT ARE EMPTY
        for i in playlist_id:
            if (len(video_id[i]) == 0):
                del video_id[i]
                playlist_id.remove(i)
        stat = {}
        comments = {}
#LOOPING THROUGH EACH PLAYLIST
        for i in playlist_id:
            stat[i] = {}
            comments[i] = {}
            likes = []
            views = []
            favorite = []
            # print(video_id[i])
#LOOPING THROUGH EACH VIDEO ID OF THAT PARTICULAR PLAYLIST
            for j in video_id[i]:
                stat[i][j] = {}
                comments[i][j] = {}
                nextPageToken = None
                while True:
                    video_idn = j
#CALLING get_video_data function to get video details
                    video_response = get_video_data(youtube, video_idn)
# CALLING get_video_comments function to get comments details
                    comments_response = get_video_comments(youtube, video_idn)
                    stat[i][j]['Likes'] = video_response['items'][0]['statistics']['likeCount']
                    stat[i][j]['Views'] = video_response['items'][0]['statistics']['viewCount']
                    stat[i][j]['favorite'] = video_response['items'][0]['statistics']['favoriteCount']
                    stat[i][j]['thumbnail'] = video_response['items'][0]['snippet']['thumbnails']['default']['url']
                    stat[i][j]['CommentCount'] = video_response['items'][0]['statistics']['commentCount']
                    count = int(video_response['items'][0]['statistics']['commentCount'])
                    stat[i][j]['Duration'] = video_response['items'][0]['contentDetails']['duration']
                    g = 1
#LOOPING THROUGH EACH COMMENT DETAILS
                    for c in comments_response['items']:
                        cid = c['snippet']['topLevelComment']['id']
                        comments[i][j]['comment' + str(g)] = {}
                        new = {}
                        new['Comment_id'] = c['snippet']['topLevelComment']['id']
                        new['Comment_Text'] = c['snippet']['topLevelComment']['snippet']['textDisplay']
                        new['Comment_Author'] = c['snippet']['topLevelComment']['snippet']['authorDisplayName']
                        new['Comment_Published'] = c['snippet']['topLevelComment']['snippet']['publishedAt']
                        comments[i][j]['comment' + str(g)] = new
                        g = g + 1
                    if not nextPageToken:
                        break
#CALLING get_channel_data FUNCTION TO GET CHANNEL DETAILS
        channel_response = get_channel_data(youtube, channel_id)
        data = {}
        channel_name = channel_response['items'][0]['snippet']['title']
        #data['channel_Data'] = {}
        data['Channel_Name'] = channel_response['items'][0]['snippet']['title']
        data['Channel_Id'] = channel_id
        data['Subscription_Count'] = channel_response['items'][0]['statistics']['subscriberCount']
        data['Channel_Views'] = channel_response['items'][0]['statistics']['viewCount']
        data['Channel_Description'] = channel_response['items'][0]['snippet']['description']
        data['video_details'] = {}
        x = 1
        z = 1
#LOOPING THROUGH EACH PLAYLIST ID
        for i, j in zip(playlist_id, playlist_title):

#LOOPING THROUGH EACH VIDEO ID
            for k in video_id[i]:
                new1 = {}
                new1['Video_Id'] = k
                new1['Video_Name'] = v_name1[k]
                new1['Playlist_Id'] = i
                new1['Playlist_Name']=j
                new1['Video_Description'] = v_description[i][k]
                new1['Published_At'] = d[i][k]['published']
                new1['Like_Count'] = stat[i][k]['Likes']
                new1['View_Count'] = stat[i][k]['Views']
                new1['Favorite_Count'] = stat[i][k]['favorite']
                new1['Comment_Count'] = stat[i][k]['CommentCount']
                new1['Duration'] = conv_duration(stat[i][k]['Duration'])
                new1['Thumbnail'] = stat[i][k]['thumbnail']
                new1['Comments'] = comments[i][k]
                data['video_details']['Video' + str(z)] = new1
                z = z + 1

        client = pym.MongoClient('mongodb://localhost:27017/')

        # CREATING A DATABASE:
        db = client["ytb"]

        # CREATING A COLLECTION:
        user_info_table = db["ytube1"]
#INSERTING THE DICTIONARY INTO MONGODB COLLECTION ytube1
        upload = user_info_table.insert_one(data)
        st.write(upload)
with col2:
    st.header(':red[Data Migration]')
    # Connect to the MongoDB server
    client = pym.MongoClient("mongodb://localhost:27017/")

    mydb = client['ytb']


    collection = mydb['ytube1']


#FUNCTION TO ACCESS EACH DOCUMENT FROM MONGODB ACCORDING TO THE CHANNEL NAME
    def fetch_document(_collection, channel_name):
        document = _collection.find_one({"Channel_Name": channel_name})
        return document

#FUNCTION TO FETCH ALL CHANNEL NAMES
    def fetch_channel_names(_collection):
        channel_names = _collection.distinct("Channel_Name")
        return channel_names

#CHANNEL TABLE CREATION
    def create_channels_table(cursor):
        create_channels_table_query = """
                CREATE TABLE IF NOT EXISTS Channels (
                    channel_id VARCHAR(255) PRIMARY KEY,
                    channel_name VARCHAR(255),
                    subscription_count INT,
                    channel_views INT,
                    channel_description MEDIUMTEXT
                
                )ENGINE = InnoDB; 
            """
        cursor.execute(create_channels_table_query)

#PLAYLIST TABLE CREATION
    def create_playlists_table(cursor):
        create_playlists_table_query = """
                CREATE TABLE IF NOT EXISTS Playlists (
                    channel_id VARCHAR(255),
                    playlist_id VARCHAR(255),
                    playlist_name VARCHAR(255),
                    PRIMARY KEY (channel_id, playlist_id),
                    FOREIGN KEY (channel_id) REFERENCES Channels(channel_id)
                )ENGINE = InnoDB;
            """
        cursor.execute(create_playlists_table_query)

#VIDEOS TABLE CREATION
    def create_videos_table(cursor):
        create_videos_table_query = """
                CREATE TABLE IF NOT EXISTS Videos (
                    video_order VARCHAR(10),
                    channel_id VARCHAR(255),
                    playlist_id VARCHAR(255),
                    video_id VARCHAR(255) PRIMARY KEY,
                    video_name VARCHAR(255),
                    video_description MEDIUMTEXT,
                    published_at DATETIME,
                    view_count INT,
                    like_count INT,
    
                    favorite_count INT,
                    comment_count INT,
                    duration VARCHAR(10),
                    thumbnail MEDIUMTEXT,
                    
                    FOREIGN KEY (channel_id) REFERENCES Channels(channel_id),
                    FOREIGN KEY (channel_id, playlist_id) REFERENCES Playlists(channel_id, playlist_id)
                )ENGINE = InnoDB;
            """
        cursor.execute(create_videos_table_query)

#COMMENTS TABLE CREATION
    def create_comments_table(cursor):
        create_comments_table_query = """
                CREATE TABLE IF NOT EXISTS Comments (
                    channel_id VARCHAR(255),
                    playlist_id VARCHAR(255),
                    video_id VARCHAR(255),
                    comment_id VARCHAR(255) PRIMARY KEY,
                    comment_text LONGTEXT,
                    comment_author VARCHAR(255),
                    comment_published_at DATETIME,
                    FOREIGN KEY (channel_id) REFERENCES Channels(channel_id),
                    FOREIGN KEY (channel_id, playlist_id) REFERENCES Playlists(channel_id, playlist_id),
                    FOREIGN KEY (video_id) REFERENCES Videos(video_id)
                )ENGINE = InnoDB;
            """
        cursor.execute(create_comments_table_query)
#FUNCTION TO MIGRATE DATA FROM mongoDB to MySQL
    def migrate_data(conn, cursor, document):

            if document['video_details'] == {}:
                st.error("Channel has no videos and can't be migrated")
                return None
            else:
#CREATE MYSQL DATABASE youtube_db
                cursor.execute("CREATE DATABASE IF NOT EXISTS youtube_db")
                cursor.execute("USE youtube_db")
#CALLING TABLE CREATION FUNCTION
                create_channels_table(cursor)
                create_playlists_table(cursor)
                create_videos_table(cursor)
                create_comments_table(cursor)
#ACCESSING VALUES FROM MONGODB TO INSERT INTO MYSQL TABLES
                channel_id = document["Channel_Id"]
                channel_name = document["Channel_Name"]
                subscription_count = document["Subscription_Count"]
                channel_views = document["Channel_Views"]
                channel_description = document["Channel_Description"]
                #channel_status = document["Channel_Details"]["Channel_Status"]
#INSERTING INTO CHANNELS TABLE
                insert_channel_query = """
                    INSERT IGNORE INTO Channels (
                        channel_id, channel_name, subscription_count,
                        channel_views, channel_description
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """
                channel_data = (channel_id, channel_name, subscription_count,
                                channel_views, channel_description)
                cursor.execute(insert_channel_query, channel_data)

                video_details = document["video_details"]

                for video_key, video_values in video_details.items():

                    playlist_id = video_values["Playlist_Id"]
                    playlist_name = video_values["Playlist_Name"]

                    # Check if playlist with the same channel_id and playlist_id exists
                    select_playlist_query = """
                        SELECT * FROM Playlists
                        WHERE channel_id = %s AND playlist_id = %s
                    """
                    cursor.execute(select_playlist_query, (channel_id, playlist_id))
                    existing_playlist = cursor.fetchone()

                    if not existing_playlist:
#INSERTING INTO PLAYLIST TABLE
                        insert_playlist_query = """
                            INSERT IGNORE INTO Playlists (channel_id, playlist_id, playlist_name)
                            VALUES (%s, %s, %s)
                        """
                        playlist_data = (channel_id, playlist_id, playlist_name)
                        cursor.execute(insert_playlist_query, playlist_data)
#ACCESSING ALL VIDEO DETAILS TO INSERT IN VIDEO TABLE
                    video_order = video_key
                    video_id = video_values["Video_Id"]
                    video_name = video_values["Video_Name"]
                    video_description = video_values["Video_Description"]
                    published_at = video_values["Published_At"]
                    view_count = video_values["View_Count"]
                    like_count = video_values["Like_Count"]
                    favorite_count = video_values["Favorite_Count"]
                    comment_count = video_values["Comment_Count"]
                    duration = video_values["Duration"]
                    thumbnail = video_values["Thumbnail"]


                    insert_video_query = """
                        INSERT IGNORE INTO Videos (
                            video_order, channel_id, playlist_id, video_id, video_name, video_description,
                            published_at, view_count, like_count, 
                            favorite_count, comment_count, duration, thumbnail
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    video_data = (video_order, channel_id, playlist_id, video_id, video_name, video_description,
                                  published_at, view_count, like_count,
                                  favorite_count, comment_count, duration, thumbnail)
                    cursor.execute(insert_video_query, video_data)
#ACCESSING COMMENTS DATA TO INSERT INTO COMMENTS TABLE
                    comments_data = video_values.get("Comments", {})

                    for _, comment_details in comments_data.items():
                        comment_id = comment_details["Comment_id"]
                        comment_text = comment_details["Comment_Text"]
                        comment_author = comment_details["Comment_Author"]
                        comment_published_at = comment_details["Comment_Published"]

                        insert_comment_query = """
                            INSERT IGNORE INTO Comments (
                                channel_id, playlist_id, video_id, comment_id,
                                comment_text, comment_author, comment_published_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """
                        comment_data = (
                            channel_id, playlist_id, video_id, comment_id,
                            comment_text, comment_author, comment_published_at
                        )
                        cursor.execute(insert_comment_query, comment_data)

                conn.commit()
                cursor.close()
                conn.close()

                st.success("Data successfully migrated to MySQL")


    add_vertical_space(2)

    st.subheader('Migrate data from MongoDB to MySQL')

    add_vertical_space(2)

    col2, col3, col4 = st.columns([4, 4, 6])

    user = col2.text_input("Enter your MySQL Username", value='rini')
    password = col3.text_input("Enter Password", value='Python@123', type='password')
#ACCESSING CHANNEL NAMES TO DISPLAY IN dropdown box for migration
    if "channel_names" not in st.session_state:
            channel_names = fetch_channel_names(collection)
            st.session_state["channel_names"] = channel_names

    existing_channel_count = len(st.session_state["channel_names"])
    new_channel_count = collection.estimated_document_count()

    if existing_channel_count != new_channel_count:
            existing_channels = set(st.session_state["channel_names"])
            new_channel_names = [name for name in fetch_channel_names(collection) if name not in existing_channels]
            st.session_state["channel_names"].extend(new_channel_names)

    selected_channel = col4.selectbox("Select a channel", st.session_state["channel_names"], key='selected_channel')

    buff1, buff2, buff3, col5 = st.columns([3, 3, 3, 2.75], gap='large')

    if col5.button("Migrate to MySQL", key='migrate'):
#SQL CONNECTION VARIABLES
            conn = mysql.connector.connect(
                host="localhost",
                user=user,
                password=password,
                charset = "utf8mb4"
            )

            cursor = conn.cursor()
            cursor.execute('SET NAMES utf8mb4')
            cursor.execute("SET CHARACTER SET utf8mb4")
            cursor.execute("SET character_set_connection=utf8mb4")
            selected_document = fetch_document(collection, selected_channel)
            if selected_document:
                migrate_data(conn, cursor, selected_document)

#TO EXECUTE SQL QUERIES
    def execute_query(conn, cursor, query):
            cursor.execute("USE youtube_db")
            cursor.execute(query)
            columns = [desc[0].replace("_", " ").title() for desc in cursor.description]
            data = cursor.fetchall()
            cursor.close()
            conn.close()
            df = pd.DataFrame(data, columns=columns)
            return df


#Defining SQL Queries

    queries = {
        "Names of all videos and their corresponding channels": """
            SELECT Videos.video_name, Channels.channel_name
            FROM Videos
            INNER JOIN Channels ON Videos.channel_id = Channels.channel_id
            ORDER BY Channels.channel_name ASC
        """,
        "Channels with the most number of videos": """
            SELECT Channels.channel_name, COUNT(Videos.video_id) AS video_count
            FROM Channels
            LEFT JOIN Videos ON Channels.channel_id = Videos.channel_id
            GROUP BY Channels.channel_name
            ORDER BY video_count DESC
            LIMIT 10
        """,
        "Top 10 most viewed videos and their respective channels": """
            SELECT Videos.video_name, Channels.channel_name, Videos.view_count
            FROM Videos
            INNER JOIN Channels ON Videos.channel_id = Channels.channel_id
            ORDER BY Videos.view_count DESC
            LIMIT 10
        """,
        "Number of comments on each video and their corresponding video names": """
            SELECT Videos.video_name, Videos.comment_count AS comment_count, Channels.channel_name
            FROM Videos
            INNER JOIN Channels ON Videos.channel_id = Channels.channel_id
            ORDER BY comment_count DESC
        """,
        "Videos with the highest number of likes and their corresponding channel names": """
        SELECT Videos.video_name, Channels.channel_name, CAST(Videos.like_count AS SIGNED) AS like_count
        FROM Videos
        INNER JOIN Channels ON Videos.channel_id = Channels.channel_id
        ORDER BY Videos.like_count DESC
        LIMIT 10
        """,
        "Total number of likes for each video and their corresponding video names": """
        SELECT Videos.video_name, Channels.channel_name, CAST(SUM(Videos.like_count) AS SIGNED) AS total_likes
        FROM Videos
        INNER JOIN Channels ON Videos.channel_id = Channels.channel_id
        GROUP BY Videos.video_name, Channels.channel_name
        """,
        "Total number of views for each channel and their corresponding channel names": """
        SELECT Channels.channel_name, CAST(SUM(Videos.view_count) AS SIGNED) AS total_views
        FROM Channels
        INNER JOIN Videos ON Channels.channel_id = Videos.channel_id
        GROUP BY Channels.channel_name
        ORDER BY total_views DESC
        """,
        "Channels that published videos in the year 2022": """
            SELECT Channels.channel_name
            FROM Channels
            INNER JOIN Videos ON Channels.channel_id = Videos.channel_id
            WHERE YEAR(Videos.published_at) = 2022
            GROUP BY Channels.channel_name
        """,
        "Average duration of all videos in each channel and their corresponding channel names": """
        SELECT Channels.channel_name, Videos.duration
        FROM Channels
        INNER JOIN Videos ON Channels.channel_id = Videos.channel_id
        WHERE Videos.duration IS NOT NULL
        """,
        "Videos with the highest number of comments and their corresponding channel names": """
            SELECT Videos.video_name, Channels.channel_name, Videos.comment_count AS comment_count
            FROM Videos
            INNER JOIN Channels ON Videos.channel_id = Channels.channel_id
            ORDER BY comment_count DESC
            LIMIT 10
        """
    }

    add_vertical_space(2)

    st.subheader(' Querying  channel data from MySQL')

    add_vertical_space(2)

    col6, buff = st.columns([25, 1])
#SELECT BOX FOR CHOOSING THE QUERY
    selected_query = col6.selectbox("Select a query", list(queries.keys()))
    runquery = st.button("Run Query", key='run')

#IF ANY QUERY IS SELECTED

    if runquery:
        #st.session_state_migrate_sql = True
        conn = mysql.connector.connect(
            host="localhost",
            user=user,
            password=password
        )
        cursor = conn.cursor()
        query = queries[selected_query]
#CALLING execute_query function to execute the choosen query
        df = execute_query(conn, cursor, query)
        df.index = df.index + 1
        st.dataframe(df, use_container_width=True)


    side_bar = st.sidebar
#
    side_bar.subheader('Youtube Data Visualization')

    selected_channel = side_bar.selectbox("Select Channel", st.session_state['channel_names'], key='channels')

    channel_data = collection.find_one({"Channel_Name": selected_channel})
    video_details = channel_data["video_details"]
#Four types of charts
    viz_options = ['Word Cloud', 'Donut Chart', 'Bar Chart', 'Histogram']

    if 'viz_options' not in st.session_state:
        st.session_state['viz_options'] = viz_options

    selected_viz = side_bar.selectbox("Select Visualization", st.session_state['viz_options'], key='selected_viz')
    viz_button = side_bar.button("Show Visualization", key='viz')

    # Viz-1

    if selected_viz == 'Word Cloud' and viz_button:

        st.subheader(f'Video Titles Word Cloud for {selected_channel} channel')
#ALL THE VIDEO TITLES WILL BE ADDED IN THE TEXT VARIABLE TO CREATE A  WORD CLOUD
        video_titles = [video_details[key]['Video_Name'] for key in video_details]
        text = ' '.join(video_titles)

        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)

        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        st.pyplot(plt, use_container_width=True)


    # Viz-2

    elif selected_viz == 'Donut Chart' and viz_button:

        st.subheader(f'Top Playlists by view count in {selected_channel} channel')

        playlist_views = {}
#FINDING THE CALCULATING THE VIEW COUNT OF EACH VIDEO
        for video_key in video_details:
            playlist_name = video_details[video_key]['Playlist_Name']
            if playlist_name == 'NA':
                continue
            view_count = int(video_details[video_key]['View_Count'])
            if playlist_name not in playlist_views:
                playlist_views[playlist_name] = view_count
            else:
#CALCULATING TOTAL VIEW COUNT FOR EACH PLAYLIST
                playlist_views[playlist_name] += view_count
#SORTING IT IN DESCENDING ORDER TO GET TOP 6
        sorted_playlists = sorted(playlist_views, key=lambda x: playlist_views[x], reverse=True)
        sorted_counts = [playlist_views[x] for x in sorted_playlists]
#STORING THE TOP 6 IN SEPARATE DATAFRAME
        top_playlists = sorted_playlists[:6]
        other_count = sum(sorted_counts[6:])
        top_counts = sorted_counts[:6] + [other_count]

        data = pd.DataFrame({'Playlist': top_playlists + ['Others'], 'View_Count': top_counts})

        fig = px.pie(data, values='View_Count', names='Playlist', hole=0.6)
        fig.update_traces(textposition='inside', textinfo='percent')

        fig.update_layout(
            showlegend=True,
            legend_title='Playlist',
            height=500,
            width=800
        )

        playlist_counts = [len([v for v in video_details.values() if v['Playlist_Name'] == playlist]) for playlist in
                           top_playlists]
        playlist_counts.append(len([v for v in video_details.values() if v['Playlist_Name'] not in top_playlists]))
        fig.update_traces(
            hovertemplate='<b>%{label}</b><br>View Count: %{value}<br>Number of Videos: %{text}<extra></extra>',
            text=playlist_counts)

        st.plotly_chart(fig, use_container_width=True)


    # Viz-3

    elif selected_viz == 'Bar Chart' and viz_button:

        st.subheader(f'Top 10 Videos by like counts in {selected_channel} channel')
#SORTING VIDEOS ACCORDING TO LIKE COUNT
        top_videos = sorted(video_details.keys(), key=lambda x: video_details[x]['Like_Count'], reverse=True)[:10]

        data = pd.DataFrame({'Video Name': [video_details[key]['Video_Name'] for key in top_videos],
                             'Like Count': [video_details[key]['Like_Count'] for key in top_videos]})

        axis_format = '~s'

        chart = alt.Chart(data).mark_bar(size=18).encode(
            x=alt.X(
                "Like Count",
                axis=alt.Axis(format=axis_format)
            ),
            y=alt.Y(
                "Video Name",
                sort='-x',
                title=None
            ),
            tooltip=[
                'Video Name', 'Like Count'
            ]
        ).properties(width=600, height=400).configure_axis(grid=False)

        st.altair_chart(chart, use_container_width=True)


    # Viz-4

    elif selected_viz == 'Histogram' and viz_button:

        st.subheader(f'Video Duration Histogram of {selected_channel} channel')

        durations = [video_details[key]['Duration'] for key in video_details]
        durations_min = [int(duration.split(':')[1]) + int(duration.split(':')[2]) / 60 for duration in durations]

        max_duration = math.ceil(max(durations_min))
        num_bins = min(max_duration, 10)

        bins = [i * max_duration / num_bins for i in range(num_bins + 1)]
        bin_labels = [f"{bins[i]:.0f}-{bins[i + 1]:.0f}" for i in range(len(bins) - 1)]
        bin_labels[-1] = f"{bins[-2]:.0f}+"

        fig_hist = go.Figure(data=[go.Histogram(x=durations_min, xbins=dict(start=bins[0], end=bins[-1],
                                                                            size=(bins[-1] - bins[0]) / num_bins))])
        fig_hist.update_layout(
            xaxis_title='Duration (in minutes)',
            yaxis_title='Count',
            showlegend=False,
            height=500,
            width=800
        )

        fig_hist.update_traces(hovertemplate='Duration: %{x:.0f} minutes<br>Count: %{y}')
        fig_hist.update_xaxes(ticktext=bin_labels, tickvals=bins[:-1])

        st.plotly_chart(fig_hist, use_container_width=True)







