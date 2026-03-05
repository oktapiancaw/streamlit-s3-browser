import asyncio

import streamlit as st
from typica import S3ConnectionMeta

from src.configs import config, project_meta
from src.connections import OpenDALConnector

st.set_page_config(page_title="S3 Connector", page_icon=":s3:", layout="wide")

st.title("S3 Connector")
st.write(f"Authors : {project_meta.authors[0].get('name')}")

left, right = st.columns(2)

if config.CONNECT_DE_STORAGE:
    from typica import DBConnectionMeta

    from connections.pmongo import MongoConnector

    mongo = MongoConnector(
        DBConnectionMeta(uri=config.CONNECT_DE_URL, database=config.CONNECT_DE_DATABASE)
    )

    try:
        list_connection = {}
        mongo.connect()
        list_connection_raw = mongo._db[config.CONNECT_DE_COLLECTION or ""].find(
            {"connection_type": "s3http"}, {"name": 1, "access": 1}
        )

        for connection in list_connection_raw.to_list():
            list_connection[f'{connection["_id"]}:{connection["name"]}'] = connection[
                "access"
            ]

        st.session_state["connections"] = list_connection

    except Exception as e:
        st.error(e)
    finally:
        mongo.close()
with left:
    custom_conn, defined_conn = st.tabs(["Custom Connection", "Defined Connection"])
    with defined_conn:
        if "connections" in st.session_state:
            st.header("Connections")
            with st.form(key="connection-list"):
                connection = st.selectbox(
                    "Connection", st.session_state["connections"].keys()
                )
                submitted = st.form_submit_button("Connect", use_container_width=True)

                if submitted:
                    st.session_state["s3"] = OpenDALConnector(
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
                            bucket=st.session_state["connections"][connection][
                                "bucket"
                            ],
                        )
                    )
        else:
            st.write("Connection didnt defined")

    with custom_conn:
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
                st.session_state["s3"] = OpenDALConnector(
                    S3ConnectionMeta(
                        endpoint=endpoint_url,
                        access_key=access_key,
                        secret_key=secret_key,
                        bucket=bucket,
                    )
                )
    if "s3" in st.session_state:
        with st.container(border=True):
            st.subheader("S3 Meta")
            st.write(st.session_state.s3._meta)

            st.subheader("Boto S3 Client")
            st.code(
                f"""
import boto3

client = boto3.client(
    "s3",
    endpoint_url="{st.session_state.s3._meta.endpoint}",
    aws_access_key_id="{st.session_state.s3._meta.access_key}",
    aws_secret_access_key="{st.session_state.s3._meta.secret_key}",
)
        """
            )
            st.subheader("Opendal Client")
            st.code(
                f"""
import opendal

client = opendal.AsyncOperator(
    "s3",
    endpoint="{st.session_state.s3._meta.endpoint}",
    access_key_id="{st.session_state.s3._meta.access_key}",
    secret_access_key="{st.session_state.s3._meta.secret_key}",
    bucket={st.session_state.s3._meta.bucket},
    region="us-east-1",
    enable_virtual_host_style="false",
)
        """
            )


def run_async(coro):
    return asyncio.run(coro)


with right:
    try:
        with st.expander("File Downloader"):
            if "s3" not in st.session_state:
                # st.error("Please connect first")
                st.stop()
            with st.form("download", border=False):
                file_path = st.text_input(
                    "File Path", value=st.session_state.get("base_path", "")
                )
                download = st.form_submit_button(
                    "Get For download", use_container_width=True
                )

                if download:
                    file_path = file_path.replace('"', "").replace("s3://", "")
                    check = run_async(st.session_state.s3.read_file(path=file_path))
                    if check:
                        st.session_state.chosen_file = file_path
                        st.session_state.chosen_data = check

            if "chosen_file" in st.session_state and "chosen_data" in st.session_state:
                with st.container(border=True):
                    col1, col2 = st.columns([7, 3])
                    with col1:
                        st.write(st.session_state.chosen_file)
                    with col2:
                        st.download_button(
                            label="Download",
                            data=st.session_state.chosen_data,
                            file_name=st.session_state.chosen_file.split("/")[-1],
                            mime="application/octet-stream",
                            use_container_width=True,
                        )

        st.session_state.s3.connect()
        with st.form("list_dir"):
            prefix = st.text_input("S3 Directory", value="")
            recursive = st.toggle("Recursive Search", value=False)

            search_dir = st.form_submit_button("Search", use_container_width=True)
            if search_dir:
                file_result, dir_result = run_async(
                    st.session_state.s3.list_dir_contents(
                        path=prefix, recursive=recursive
                    )
                )
                st.session_state.dir_result = dir_result
                st.session_state.file_result = file_result

        if "dir_result" in st.session_state or "file_result" in st.session_state:
            with st.container(border=True):
                dir_tab, file_tab, raw_json_tab = st.tabs(
                    ["Folder Directories", "File List", "Raw JSON"]
                )
                page_size = 10
                with dir_tab:
                    if "dir_page_number" not in st.session_state:
                        st.session_state.dir_page_number = 0
                    total_pages = len(st.session_state.dir_result) // page_size

                    dir_tab_cols = st.columns(3)

                    if dir_tab_cols[0].button("Previous", key="dir_prev"):
                        st.session_state.dir_page_number -= (
                            1 if st.session_state.dir_page_number >= 1 else 0
                        )
                    if dir_tab_cols[2].button("Next", key="dir_next"):
                        st.session_state.dir_page_number += (
                            1 if st.session_state.dir_page_number < total_pages else 0
                        )

                    dir_tab_cols[1].write(
                        f"{st.session_state.dir_page_number + 1} / {total_pages + 1}"
                    )

                    # Ensure page number stays within bounds
                    st.session_state.dir_page_number = max(
                        0, min(st.session_state.dir_page_number, total_pages)
                    )

                    # 4. Display Data
                    dir_start_idx = st.session_state.dir_page_number * page_size
                    dir_end_idx = dir_start_idx + page_size

                    for values in st.session_state.dir_result[
                        dir_start_idx:dir_end_idx
                    ]:
                        st.code(values.get("Key"), language="python")
                        metaDate, metaSize = st.columns(2)
                        with metaDate:
                            st.write(values.get("LastModified"))
                        with metaSize:
                            st.write(round(values.get("Size") / 1024, 2), "KB")
                    st.write(
                        f"Total Folder: {len(st.session_state.dir_result[dir_start_idx:dir_end_idx])} from {len(st.session_state.dir_result)}"
                    )
                with file_tab:
                    if "file_page_number" not in st.session_state:
                        st.session_state.file_page_number = 0
                    total_pages = len(st.session_state.file_result) // page_size

                    file_tab_cols = st.columns(3)

                    if file_tab_cols[0].button("Previous", key="file_prev"):
                        st.session_state.file_page_number -= (
                            1 if st.session_state.file_page_number >= 1 else 0
                        )
                    if file_tab_cols[2].button("Next", key="file_next"):
                        st.session_state.file_page_number += (
                            1 if st.session_state.file_page_number < total_pages else 0
                        )

                    file_tab_cols[1].write(
                        f"{st.session_state.file_page_number + 1} / {total_pages + 1}"
                    )

                    # Ensure page number stays within bounds
                    st.session_state.file_page_number = max(
                        0, min(st.session_state.file_page_number, total_pages)
                    )

                    # 4. Display Data
                    file_start_idx = st.session_state.file_page_number * page_size
                    file_end_idx = file_start_idx + page_size

                    for values in st.session_state.file_result[
                        file_start_idx:file_end_idx
                    ]:
                        st.code(values.get("Key"), language="python")
                        metaDate, metaSize, metaDownload = st.columns([6, 2, 2])
                        with metaDate:
                            st.write(values.get("LastModified"))
                        with metaSize:
                            st.write(round(values.get("Size") / 1024, 2), "KB")
                        with metaDownload:
                            st.download_button(
                                label="Download",
                                data=run_async(
                                    st.session_state.s3.read_file(
                                        path=values.get("Key")
                                    )
                                ),
                                file_name=values.get("Key").split("/")[-1],
                                mime="application/octet-stream",
                                use_container_width=True,
                            )
                    st.write(
                        f"Total File: {len(st.session_state.file_result[file_start_idx:file_end_idx])} from {len(st.session_state.file_result)}"
                    )
                with raw_json_tab:
                    st.json(
                        {
                            "folders": st.session_state.dir_result,
                            "total_keys": len(st.session_state.file_result),
                            "keys": st.session_state.file_result,
                        },
                        expanded=False,
                    )
                # if st.session_state.file_result:
                #     with st.expander("List Folder"):
                # if file_result:
                #     with st.expander("List Files"):
                #         for values in file_result:
                #             st.code(values.get("Key"), language="python")
                #             metaDate, metaSize, metaType = st.columns(3)
                #             with metaDate:
                #                 st.write(values.get("LastModified"))
                #             with metaSize:
                #                 st.write(round(values.get("Size") / 1024, 2), "KB")
                #             with metaType:
                #                 st.write(values.get("ContentType"))

    except Exception as e:
        st.error(e)
    finally:
        st.session_state.s3.close()
