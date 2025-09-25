import pathway as pw

# Define the schema to read both caption and format from the CSV
class MemeSchema(pw.Schema):
    caption: str
    format: str

# Step 1: Ingest memes from CSV in streaming mode.
# Pathway will watch this file for any new memes you add.
memes = pw.io.csv.read(
    "data/memes.csv",
    schema=MemeSchema,
    mode="streaming",
    autocommit_duration_ms=1000,
)

# Step 2: Calculate real-time trending formats.
# We group by the 'format' column and count how many times each format appears.
trending_formats = memes.groupby(memes.format).reduce(
    format=memes.format, count=pw.reducers.count(memes.caption)
)

# Step 3: Write the live results to a JSON Lines file.
# Your FastAPI server will read this file to get the latest trends.
pw.io.jsonlines.write(trending_formats, "data/trending_formats.jsonl")

# Step 4: Run the pipeline.
# This will start the process and keep it running to watch for new data.
if __name__ == "__main__":
    pw.run()