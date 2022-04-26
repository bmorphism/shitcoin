import hashlib
import argparse


def cw20_ibc_denom(port_id, channel_id, address):
    prefix = f"{port_id}/{channel_id}"
    denom = f"{prefix}/{address}"
    return f"ibc/{hashlib.sha256(denom.encode('utf-8')).hexdigest().upper()}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port_id", type=str, required=True)
    parser.add_argument("--channel_id", type=str, required=True)
    parser.add_argument("--address", type=str, required=True)
    args = parser.parse_args()
    print(cw20_ibc_denom(args.port_id, args.channel_id, args.address))


if __name__ == "__main__":
    main()
