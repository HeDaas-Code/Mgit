# MGit Copilot Configuration Example

This file shows example configuration for the Copilot feature.

## Configuration Location

The copilot configuration is stored in MGit's config file (managed by ConfigManager).
Typically located at: `~/.config/mgit/config.json` or similar location depending on your OS.

## Configuration Keys

```json
{
  "copilot": {
    "enabled": true,
    "api_key": "your-siliconflow-api-key-here",
    "model": "Qwen/Qwen2.5-7B-Instruct"
  }
}
```

## Available Models

You can use any of these models with SiliconFlow:

### Qwen Series (Recommended)
- `Qwen/Qwen2.5-7B-Instruct` - Best balance of speed and quality (default)
- `Qwen/Qwen2.5-14B-Instruct` - Higher quality, slightly slower
- `Qwen/Qwen2.5-32B-Instruct` - Highest quality, slower

### DeepSeek
- `deepseek-ai/DeepSeek-V2.5` - Strong reasoning, good for technical content

### Meta LLaMA
- `meta-llama/Meta-Llama-3.1-8B-Instruct` - Open source alternative

## Getting API Key

1. Visit https://siliconflow.cn
2. Register or login to your account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key to Copilot settings in MGit

## Configuration via UI

The recommended way to configure Copilot is through the UI:

1. Open MGit
2. Go to menu: `Copilot > Copilot设置`
3. Enter your API key
4. Select your preferred model
5. Check "启用 Copilot"
6. Click "测试连接" to verify
7. Click "保存"

## Security Notes

- API keys are stored in plain text in local configuration file
- Ensure proper file system permissions to protect configuration files
- Never commit configuration files with API keys to git
- Use environment variables for CI/CD if needed

## Environment Variables (Optional)

You can also set API key via environment variable:

```bash
export SILICONFLOW_API_KEY="your-api-key-here"
```

Note: UI configuration takes precedence over environment variables.

## Troubleshooting

### API Key Not Working
- Verify key is correct (no extra spaces)
- Check account balance on SiliconFlow
- Ensure network connectivity
- Try "测试连接" in settings dialog

### Model Not Available
- Some models may require specific API tier
- Check SiliconFlow documentation for model availability
- Try using default model first

### Connection Timeout
- Check internet connection
- Verify firewall settings
- Try increasing timeout in code if needed

## Advanced Configuration

For advanced users, you can modify additional parameters by editing the source code:

- `temperature`: Controls randomness (0.0-1.0), in copilot_manager.py
- `max_tokens`: Maximum output length, in copilot_manager.py
- API timeout: In siliconflow_client.py

## Rate Limits

Be aware of SiliconFlow API rate limits:
- Free tier: Limited requests per minute
- Paid tiers: Higher limits

Check your plan at https://siliconflow.cn

## Support

For issues or questions:
- Check the [Copilot Guide](./copilot_guide.md)
- Submit GitHub issue
- Contact SiliconFlow support for API issues
