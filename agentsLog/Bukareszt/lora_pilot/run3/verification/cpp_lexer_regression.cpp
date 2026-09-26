#include "jinja/lexer.h"
#include <cstdio>
#include <fstream>
#include <sstream>
int main(int argc,char**argv){ std::ifstream f(argv[1],std::ios::binary); std::stringstream ss; ss<<f.rdbuf(); std::string s=ss.str();
 const char* cases[][2]={{"raw",nullptr},{"two_nl","x{{ a }}\n\n"},{"trail_space_nl","x{{ a }} \n"},{"crlf_end","x\r\n{{ a }}\r\n"},{"lone_cr_end","x\r{{ a }}\r"},{"lead_ws"," \n{{ a }}\n"}};
 for(auto&c:cases){ std::string in=c[1]?c[1]:s; jinja::lexer lx; auto r=lx.tokenize(in); fwrite(c[0],1,strlen(c[0]),stdout); printf("\t%zu\t",r.source.size()); for(unsigned char ch: (c[1]?r.source:std::string())) printf("%02x",ch); printf("\n"); if(!c[1]){ std::ofstream o("cpp_normalized_raw.bin",std::ios::binary); o<<r.source; } }
}
