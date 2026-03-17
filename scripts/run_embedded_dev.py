import sys
import uvicorn


def main() -> None:
    # Force optional Kerberos support to stay disabled in the embedded runtime.
    sys.modules["gssapi"] = None
    sys.path.insert(0, r"c:\Users\nithi\OneDrive\Desktop\Dicippline_Bot")
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    main()
