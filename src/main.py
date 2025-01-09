import streamlit as st

from configs import config, poetry_config
from connections.s3 import S3HttpConnector
from models.base import S3ConnectionMeta

st.set_page_config(page_title="S3 Connector", page_icon=":s3:", layout="wide")

st.title("S3 Connector")
st.write(f"Authors : {poetry_config.authors[0]}")

left, right = st.columns(2)

if config.CONNECT_DE_STORAGE:
    from connections.pmongo import MongoConnector
    from typica import DBConnectionMeta

    mongo = MongoConnector(
        DBConnectionMeta(uri=config.CONNECT_DE_URL, database=config.CONNECT_DE_DATABASE)
    )

    try:
        list_connection = {}
        with mongo.stream_connect() as client:
            list_connection_raw = client.db["connections_v2"].find(
                {"connection_type": "s3http"}, {"name": 1, "access": 1}
            )

            for connection in list_connection_raw.to_list():
                list_connection[f'{connection["_id"]}:{connection["name"]}'] = (
                    connection["access"]
                )

            st.session_state["connections"] = list_connection

    except Exception as e:
        st.error(e)
with left:

    if "connections" in st.session_state:
        st.header("Connections")
        with st.form(key="connection-list"):
            connection = st.selectbox(
                "Connection", st.session_state["connections"].keys()
            )
            submitted = st.form_submit_button("Connect", use_container_width=True)

            if submitted:
                st.session_state["s3"] = S3HttpConnector(
                    S3ConnectionMeta(
                        endpoint_url=st.session_state["connections"][connection][
                            "endpoint_url"
                        ],
                        access_key=st.session_state["connections"][connection][
                            "access_key"
                        ],
                        secret_key=st.session_state["connections"][connection][
                            "secret_key"
                        ],
                        bucket=st.session_state["connections"][connection]["bucket"],
                    )
                )

    with st.form(key="connection"):
        endpoint_url = st.text_input("Endpoint URL", value="http://localhost:9000")
        col1, col2 = st.columns(2)
        with col1:
            access_key = st.text_input("Access Key", value="minioadmin")
        with col2:
            secret_key = st.text_input(
                "Secret Key", value="minioadmin", type="password"
            )
        bucket = st.text_input("Bucket", value="my-bucket")

        submitted = st.form_submit_button("Connect", use_container_width=True)
        if submitted:
            st.session_state["s3"] = S3HttpConnector(
                S3ConnectionMeta(
                    endpoint_url=endpoint_url,
                    access_key=access_key,
                    secret_key=secret_key,
                    bucket=bucket,
                )
            )
    if "s3" in st.session_state:
        with st.container(border=True):
            st.subheader("S3 Meta")
            st.write(st.session_state.s3.s3_meta)

            st.subheader("S3 Client")
            st.code(
                f"""
import boto3

client = boto3.client(
    "s3",
    endpoint_url="{st.session_state.s3._meta.endpoint_url}",
    aws_access_key_id="{st.session_state.s3._meta.access_key}",
    aws_secret_access_key="{st.session_state.s3._meta.secret_key}",
)
        """
            )

with right:
    try:
        if "s3" not in st.session_state:
            # st.error("Please connect first")
            st.stop()
        st.session_state.s3.connect()
        with st.form("list_dir"):

            prefix = st.text_input("S3 Directory", value="")
            only_folder = st.toggle("Only Folder", value=True)
            full_path = st.toggle("Full Path", value=False)

            search_dir = st.form_submit_button("Search", use_container_width=True)
            if search_dir:
                check = st.session_state.s3.client.list_objects(
                    Bucket=st.session_state.s3.bucket, Prefix=prefix, Delimiter="/"
                )

                clean_folders = []
                clean_keys = []
                file_metas = {}
                for folder in check.get("CommonPrefixes", []):
                    clean_folders.append(folder.get("Prefix").replace(prefix, ""))
                if not only_folder:
                    paginator = st.session_state.s3.client.get_paginator(
                        "list_objects_v2"
                    )
                    for page in paginator.paginate(
                        Bucket=st.session_state.s3.bucket, Prefix=prefix
                    ):
                        for file in page.get("Contents", []):
                            if not file.get("Key").endswith("/"):
                                clean_key = None
                                if not full_path:
                                    clean_key = file.get("Key").replace(prefix, "")
                                else:
                                    clean_key = file.get("Key")
                                if clean_key:
                                    file_metas.update(
                                        {
                                            file.get("Key"): {
                                                "path": clean_key,
                                                "size": file.get("Size"),
                                                "last_modified": file.get(
                                                    "LastModified"
                                                ),
                                            }
                                        }
                                    )
                                    clean_keys.append(clean_key)
                    clean_keys = list(set(clean_keys) - set(clean_folders))

                st.json(
                    {
                        "folders": clean_folders,
                        "total_keys": len(clean_keys),
                        "keys": clean_keys,
                    }
                )
                with st.expander("List Files"):
                    for key, values in file_metas.items():
                        st.code(values.get("path"), language="python")
                        metaDate, metaSize = st.columns(2)
                        with metaDate:
                            st.write(values.get("last_modified"))
                        with metaSize:
                            st.write(round(values.get("size") / 1024, 2), "KB")

                if not full_path:
                    st.session_state["base_path"] = prefix
                else:
                    st.session_state["base_path"] = f""
        with st.form("download"):
            file_path = st.text_input(
                "File Path", value=st.session_state.get("base_path", "")
            )
            download = st.form_submit_button(
                "Get For download", use_container_width=True
            )

            if download:
                file_path = file_path.replace('"', "").replace("s3://", "")
                check = st.session_state.s3.client.get_object(
                    Bucket=st.session_state.s3.bucket, Key=file_path
                )
                if check.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
                    st.session_state.chosen_file = file_path
                    st.session_state.chosen_data = check.get("Body")

        if "chosen_file" in st.session_state and "chosen_data" in st.session_state:
            with st.container(border=True):
                col1, col2 = st.columns([7, 3])
                with col1:
                    st.write(st.session_state.chosen_file)
                with col2:
                    st.download_button(
                        label="Download",
                        data=st.session_state.chosen_data.read(),
                        file_name=st.session_state.chosen_file.split("/")[-1],
                        mime="application/octet-stream",
                        use_container_width=True,
                    )
    except Exception as e:
        st.error(e)
    finally:
        st.session_state.s3.close()
