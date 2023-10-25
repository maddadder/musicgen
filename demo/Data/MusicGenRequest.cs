using System.Text.Json.Serialization;
namespace demo.Data;


public class MusicGenRequest
{
    [JsonPropertyName("text")]
    public string Text { get; set; }

    [JsonPropertyName("duration")]
    public string Duration { get; set; }

    [JsonPropertyName("audio_file")]
    public string AudioFile { get; set; }
    [JsonPropertyName("speech2text")]
    public bool Speech2Text { get; set; }
}
