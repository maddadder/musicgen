using System.IO;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Components.Forms;

public class FileUploadService
{
    public async Task<string> SaveFile(IBrowserFile file)
    {
        using (var memoryStream = new MemoryStream())
        {
            await file.OpenReadStream().CopyToAsync(memoryStream);
            var fileContent = memoryStream.ToArray();
            return Convert.ToBase64String(fileContent);
        }
    }
}
