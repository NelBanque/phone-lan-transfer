"""Receive one authenticated file directly from a streamed HTTP body."""

import errno
from collections.abc import Iterator

from anyio import from_thread
from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.requests import ClientDisconnect

from phone_lan_transfer.access import require_access_token
from phone_lan_transfer.config import TransferSettings
from phone_lan_transfer.storage import FileTooLargeError, save_file

router = APIRouter()


def request_chunks(request: Request) -> Iterator[bytes]:
    """Pull async network chunks from the endpoint's AnyIO worker thread."""
    stream = request.stream()
    while True:
        try:
            chunk = from_thread.run(stream.__anext__)
        except StopAsyncIteration:
            return
        yield chunk


@router.post("/uploads", status_code=201, dependencies=[Depends(require_access_token)])
def upload_file(request: Request, destination_name: str) -> dict[str, str]:
    """Save the raw request body using this server run's destination and limit."""
    settings: TransferSettings = request.app.state.transfer_settings
    try:
        saved_path = save_file(
            request_chunks(request),
            settings.destination_directory,
            destination_name,
            max_bytes=settings.max_file_bytes,
        )
    except FileTooLargeError as error:
        raise HTTPException(status_code=413, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileExistsError as error:
        raise HTTPException(
            status_code=409, detail="A file with this destination name already exists"
        ) from error
    except ClientDisconnect as error:
        raise HTTPException(status_code=400, detail="Upload interrupted") from error
    except OSError as error:
        if error.errno == errno.ENOSPC:
            raise HTTPException(
                status_code=507, detail="Not enough space to save this file"
            ) from error
        raise HTTPException(
            status_code=500, detail="Could not save this file in the destination folder"
        ) from error

    return {"status": "saved", "destination_name": saved_path.name}
