import asyncio

try:
    from e2b import AsyncTemplate, default_build_logger
except Exception as e:
    raise SystemExit(f"e2b SDK missing or incompatible: {e}")


async def main():
    # Minimal base image; customize if needed
    template = AsyncTemplate().from_image("e2bdev/base")

    await AsyncTemplate.build(
        template,
        alias="vot-guardian-cpu",
        on_build_logs=default_build_logger(),
    )


if __name__ == "__main__":
    asyncio.run(main())
