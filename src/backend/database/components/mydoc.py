from database.base import db_cursor


def get_user_list():
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT id, user_name, email
            FROM "user"
            ORDER BY user_name
            """
        )

        rows = cur.fetchall()
        return [
            {
                "id": r[0],
                "user_name": r[1],
                "email": r[2]
            }
            for r in rows
        ]


def get_doc_list(user_id: str):
    try:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT
                    d.room_id,
                    d.room_name,
                    d.create_time,
                    d.overall_permission,

                    p.user_id AS perm_user_id,
                    p.permission,

                    u.user_name,
                    u.email
                FROM document d
                LEFT JOIN permission p
                    ON d.room_id = p.room_id
                    AND p.permission IN (2, 3)
                LEFT JOIN "user" u
                    ON p.user_id = u.id
                WHERE d.owner_user_id = %s
                ORDER BY d.create_time DESC
                """,
                (user_id,)
            )

            rows = cur.fetchall()

        # ---------- Python 组装 ----------
        docs = {}
        for r in rows:
            room_id = r[0]

            if room_id not in docs:
                docs[room_id] = {
                    "room_id": r[0],
                    "room_name": r[1],
                    "create_time": r[2],
                    "overall_permission": r[3],
                    "permissions": {}
                }

            perm_user_id = r[4]
            if perm_user_id is None:
                continue

            docs[room_id]["permissions"][perm_user_id] = {
                "id": perm_user_id,
                "user_name": r[6],
                "email": r[7],
                "permission": r[5],
            }

        return list(docs.values())

    except Exception as e:
        print(f"获取文档列表失败: {e}")
        return []


def update_visibility_dataset(room_id, overall_permission):
    with db_cursor() as cur:
        cur.execute(
            """
            UPDATE document
            SET overall_permission = %s
            WHERE room_id = %s
            """,
            (overall_permission, room_id)
        )
        return cur.rowcount > 0


def add_user_permission_dataset(room_id, user_id, permission):
    with db_cursor() as cur:
        cur.execute(
            """
            MERGE INTO permission t
            USING (
                SELECT %s AS room_id, %s AS user_id, %s AS permission
            ) s
            ON (t.room_id = s.room_id AND t.user_id = s.user_id)
            WHEN MATCHED THEN
                UPDATE SET permission = s.permission
            WHEN NOT MATCHED THEN
                INSERT (room_id, user_id, permission)
                VALUES (s.room_id, s.user_id, s.permission)
            """,
            (room_id, user_id, permission)
        )
        return True


def remove_user_dataset(room_id, user_id):
    with db_cursor() as cur:
        cur.execute(
            """
            DELETE FROM permission
            WHERE room_id = %s
              AND user_id = %s
            """,
            (room_id, user_id)
        )
        return cur.rowcount > 0
    

def change_user_permission_dataset(room_id, user_id, permission):
    with db_cursor() as cur:
        cur.execute(
            """
            UPDATE permission
            SET permission = %s
            WHERE room_id = %s
              AND user_id = %s
            """,
            (permission, room_id, user_id)
        )
        return cur.rowcount > 0


def change_room_name_dataset(room_id, room_name):
    with db_cursor() as cur:
        cur.execute(
            """
            UPDATE document
            SET room_name = %s
            WHERE room_id = %s
            """,
            (room_name, room_id)
        )
        return cur.rowcount > 0


def delete_room_dataset(room_id):
    with db_cursor() as cur:
        # 删除权限
        cur.execute(
            "DELETE FROM permission WHERE room_id = %s",
            (room_id,)
        )

        # 删除内容
        cur.execute(
            "DELETE FROM content WHERE room_id = %s",
            (room_id,)
        )

        # 删除文档
        cur.execute(
            "DELETE FROM document WHERE room_id = %s",
            (room_id,)
        )

        return cur.rowcount > 0
