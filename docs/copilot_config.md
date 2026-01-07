# MGit Copilot Configuration Example

This file shows example configuration for the Copilot feature.

## Configuration Location

The copilot configuration is stored in MGit's config file (managed by ConfigManager).
Typically located at: `~/.config/mgit/config.json` or similar location depending on your OS.

## Configuration Keys

### SiliconFlow Provider (Default)

```json
{
  "copilot": {
    "enabled": true,
    "provider": "siliconflow",
    "api_key": "your-siliconflow-api-key-here",
    "model": "Qwen/Qwen2.5-7B-Instruct"
  }
}
```

### ModelScope API-Inference Provider

```json
{
  "copilot": {
    "enabled": true,
    "provider": "modelscope",
    "api_key": "your-modelscope-api-key-here",
    "model": "qwen/Qwen2.5-7B-Instruct"
  }
}
```

## Providers

MGit Copilot now supports two LLM service providers:

### 1. SiliconFlow (Default)
- **Website**: https://siliconflow.cn
- **API Documentation**: https://docs.siliconflow.cn
- **Features**: Fast inference, multiple models, competitive pricing
- **Provider ID**: `siliconflow`

### 2. ModelScope API-Inference (New!)
- **Website**: https://www.modelscope.cn
- **API Documentation**: https://www.modelscope.cn/docs/model-service/API-Inference/intro
- **Features**: Official Alibaba Cloud service, reliable infrastructure
- **Provider ID**: `modelscope`

## Available Models

### SiliconFlow Models

You can use any of these models with SiliconFlow:

#### Qwen Series (Recommended)
- `Qwen/Qwen2.5-7B-Instruct` - Best balance of speed and quality (default)
- `Qwen/Qwen2.5-14B-Instruct` - Higher quality, slightly slower
- `Qwen/Qwen2.5-32B-Instruct` - Highest quality, slower

#### DeepSeek
- `deepseek-ai/DeepSeek-V2.5` - Strong reasoning, good for technical content

#### Meta LLaMA
- `meta-llama/Meta-Llama-3.1-8B-Instruct` - Open source alternative

### ModelScope API-Inference Models

Available models with ModelScope:

#### Qwen Series
- `qwen/Qwen2.5-7B-Instruct` - Best balance of speed and quality (default)
- `qwen/Qwen2.5-14B-Instruct` - Higher quality
- `qwen/Qwen2.5-32B-Instruct` - Highest quality

**Note**: Model names use lowercase namespace with ModelScope (e.g., `qwen/` instead of `Qwen/`)

## Getting API Key

### For SiliconFlow

1. Visit https://siliconflow.cn
2. Register or login to your account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key to Copilot settings in MGit

### For ModelScope

1. Visit https://www.modelscope.cn
2. Register or login with your Alibaba Cloud account
3. Navigate to the API-Inference section
4. Create a new API key
5. Copy the key to Copilot settings in MGit

## Configuration via UI

The recommended way to configure Copilot is through the UI:

1. Open MGit
2. Go to menu: `Copilot > Copilot设置`
3. Select your preferred provider (SiliconFlow or ModelScope)
4. Enter your API key
5. Select your preferred model
6. Check "启用 Copilot"
7. Click "测试连接" to verify
8. Click "保存"

## Switching Between Providers

You can switch between SiliconFlow and ModelScope at any time:

1. Open Copilot settings
2. Select different provider from dropdown
3. Enter the API key for the new provider
4. Select an appropriate model for that provider
5. Test connection and save

**Note**: Each provider requires its own API key. Make sure to obtain and configure API keys for both providers if you plan to switch between them.

## Security Notes

- API keys are stored in plain text in local configuration file
- Ensure proper file system permissions to protect configuration files
- Never commit configuration files with API keys to git
- Use environment variables for CI/CD if needed

## Environment Variables (Optional)

You can also set API key via environment variable:

### For SiliconFlow
```bash
export SILICONFLOW_API_KEY="your-api-key-here"
```

### For ModelScope
```bash
export MODELSCOPE_API_KEY="your-api-key-here"
```

Note: UI configuration takes precedence over environment variables.

## Troubleshooting

### API Key Not Working
- Verify key is correct (no extra spaces)
- Check account balance on your provider's website
- Ensure network connectivity
- Try "测试连接" in settings dialog
- Verify you're using the correct API key for the selected provider

### Model Not Available
- Some models may require specific API tier or region
- Check provider documentation for model availability
- Try using default model first
- For ModelScope: Ensure model name uses correct case (lowercase namespace)
- For SiliconFlow: Ensure model name uses correct case (uppercase namespace)

### Connection Timeout
- Check internet connection
- Verify firewall settings
- Try increasing timeout in code if needed
- Some regions may have slower access to certain providers

### Provider-Specific Issues

#### SiliconFlow
- Check status at https://siliconflow.cn
- Verify API tier and quotas
- Review rate limits

#### ModelScope
- Check Alibaba Cloud account status
- Verify API-Inference service is enabled
- Review service quotas and limits
- Check region availability

## Advanced Configuration

For advanced users, you can modify additional parameters by editing the source code:

- `temperature`: Controls randomness (0.0-1.0), in copilot_manager.py
- `max_tokens`: Maximum output length, in copilot_manager.py
- API timeout: In siliconflow_client.py

## Rate Limits

Be aware of API rate limits from your provider:

### SiliconFlow
- Free tier: Limited requests per minute
- Paid tiers: Higher limits
- Check your plan at https://siliconflow.cn

### ModelScope API-Inference
- Limits depend on your Alibaba Cloud account tier
- Check quotas in your ModelScope console
- Visit https://www.modelscope.cn for details

## Support

For issues or questions:
- Check the [Copilot Guide](./copilot_guide.md)
- Submit GitHub issue for MGit-related problems
- Contact SiliconFlow support for SiliconFlow API issues
- Contact Alibaba Cloud support for ModelScope API issues
