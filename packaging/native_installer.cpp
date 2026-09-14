#include <windows.h>
#include <fstream>
#include <string>
#include <vector>
#include <cstdint>
#include <cstdlib>
#include <algorithm>

int main() {
  char exeBuf[MAX_PATH]; GetModuleFileNameA(nullptr, exeBuf, MAX_PATH);
  std::ifstream in(exeBuf, std::ios::binary); if (!in) return 1;
  in.seekg(0, std::ios::end); const std::streamoff end=in.tellg();
  if(end<14) return 2; in.seekg(end-14);
  char marker[6]; std::uint64_t len=0; in.read(marker,6); in.read(reinterpret_cast<char*>(&len),8);
  if(std::string(marker,6)!="DTWZIP" || len>(std::uint64_t)(end-14)) return 3;
  in.seekg(end-14-(std::streamoff)len);
  char tempDir[MAX_PATH]; GetTempPathA(MAX_PATH,tempDir); char tempBuf[MAX_PATH]; wsprintfA(tempBuf,"%sDigitalTimeWheelPayload-%lu.zip",tempDir,(unsigned long)GetCurrentProcessId()); std::string tempA=tempBuf;
  std::ofstream out(tempA,std::ios::binary); std::vector<char> buf(1<<20); std::uint64_t left=len;
  while(left){auto n=(std::streamsize)std::min<std::uint64_t>(buf.size(),left);in.read(buf.data(),n);out.write(buf.data(),n);left-=n;} out.close();
  char local[MAX_PATH]; GetEnvironmentVariableA("LOCALAPPDATA",local,MAX_PATH); char targetBuf[MAX_PATH]; wsprintfA(targetBuf,"%s\\DigitalTimeWheel",local); std::string targetA=targetBuf;
  int need=MultiByteToWideChar(CP_ACP,0,tempA.c_str(),-1,nullptr,0); std::wstring qtemp(need,0); MultiByteToWideChar(CP_ACP,0,tempA.c_str(),-1,&qtemp[0],need); qtemp.pop_back();
  need=MultiByteToWideChar(CP_ACP,0,targetA.c_str(),-1,nullptr,0); std::wstring qtarget(need,0); MultiByteToWideChar(CP_ACP,0,targetA.c_str(),-1,&qtarget[0],need); qtarget.pop_back();
  std::wstring cmd=L"powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \"Expand-Archive -LiteralPath '"+qtemp+L"' -DestinationPath '"+qtarget+L"' -Force; & '"+qtarget+L"\\packaging\\install.ps1' -Payload '"+qtemp+L"' -SkipExtract\"";
  STARTUPINFOW si{}; si.cb=sizeof(si); PROCESS_INFORMATION pi{}; std::vector<wchar_t> mutableCmd(cmd.begin(),cmd.end()); mutableCmd.push_back(0);
  BOOL ok=CreateProcessW(nullptr,mutableCmd.data(),nullptr,nullptr,FALSE,CREATE_NO_WINDOW,nullptr,nullptr,&si,&pi); if(!ok) return 4;
  WaitForSingleObject(pi.hProcess,INFINITE); DWORD code=1; GetExitCodeProcess(pi.hProcess,&code); CloseHandle(pi.hThread);CloseHandle(pi.hProcess); DeleteFileA(tempA.c_str()); return (int)code;
}
