PAYLOAD_FILE="payload/primary_nova.json"

aws lambda invoke \
    --function-name alphonse_email_summarizer \
    --payload file://${PAYLOAD_FILE} \
    output.txt
