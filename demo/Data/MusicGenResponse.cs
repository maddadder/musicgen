using System.Text.Json.Serialization;

namespace demo.Data;

public class MusicGenResponse
{
    [JsonPropertyName("text")]
    public string Text { get; set; }

    [JsonPropertyName("result")]
    public string Result { get; set; }
    
    [JsonPropertyName("audio_data")]
    public string audio_data { get; set; }
}
