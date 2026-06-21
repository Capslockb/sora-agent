/**
 * Gemini Audio Worklet Processor
 *
 * AudioWorklet processor for capturing microphone audio at 16kHz.
 * Runs in a separate thread to avoid blocking the main thread.
 */
class GeminiAudioProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super();
    const processorOptions = options?.processorOptions;
    this.bufferSize = processorOptions?.bufferSize ?? 2048;
    this.buffer = new Float32Array(this.bufferSize);
    this.bufferIndex = 0;
    this.stopped = false;
    this.port.onmessage = (event) => {
      if (event.data.type === 'stop') {
        this.stopped = true;
      }
    };
  }

  process(inputs, _outputs, _parameters) {
    if (this.stopped) return false;
    const input = inputs[0];
    if (!input || input.length === 0) return true;
    const channelData = input[0];
    if (!channelData || channelData.length === 0) return true;
    for (let i = 0; i < channelData.length; i++) {
      this.buffer[this.bufferIndex++] = channelData[i];
      if (this.bufferIndex >= this.bufferSize) {
        this.sendBuffer();
        this.bufferIndex = 0;
      }
    }
    return true;
  }

  sendBuffer() {
    const int16Data = new Int16Array(this.bufferSize);
    for (let i = 0; i < this.bufferSize; i++) {
      const sample = Math.max(-1, Math.min(1, this.buffer[i]));
      int16Data[i] = sample < 0 ? Math.round(sample * 0x8000) : Math.round(sample * 0x7fff);
    }
    this.port.postMessage({ type: 'audio', data: int16Data }, [int16Data.buffer]);
  }
}

registerProcessor('gemini-audio-processor', GeminiAudioProcessor);
