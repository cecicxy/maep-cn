"""MAEP-CN server entry point."""

import argparse
import uvicorn
from dotenv import load_dotenv


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="MAEP-CN API Server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--db", default="maep.db")
    args = parser.parse_args()

    import os
    os.environ["DB_PATH"] = args.db

    from api.app import create_app
    app = create_app(db_path=args.db)

    print(f"MAEP-CN server starting at http://{args.host}:{args.port}")
    print(f"Database: {args.db}")
    print(f"Open http://{args.host}:{args.port} in your browser")

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
