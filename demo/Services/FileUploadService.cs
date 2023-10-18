using System.IO;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Components.Forms;

public static class FileUploadServiceHelper
{
    public const long MAXALLOWEDSIZE = 1024000;
}

public class FileUploadService
{
    public async Task<string> SaveFile(IBrowserFile file)
    {
        using (var memoryStream = new MemoryStream())
        {
            await file.OpenReadStream(FileUploadServiceHelper.MAXALLOWEDSIZE).CopyToAsync(memoryStream);
            var fileContent = memoryStream.ToArray();
            return Convert.ToBase64String(fileContent);
        }
    }
}
