/*
 * Catroid: An on-device visual programming system for Android devices
 * Copyright (C) 2010-2016 The Catrobat Team
 * (<http://developer.catrobat.org/credits>)
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * An additional term exception under section 7 of the GNU Affero
 * General Public License, version 3, is available at
 * http://developer.catrobat.org/license_additional_term
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
#include <curses.h>
#include <stdio.h>
#include <stdlib.h>
#include <menu.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <curl/curl.h>


WINDOW *win;
WINDOW *menuwin;
ITEM **it;
MENU *menu;
int menuquit = 0;
int num_items = 0;
int x, y;
char* init_template_file = "init_template";
char* init_script_file = "/etc/init.d/RaspberInoServer";
char* init_script_file_stop = "/etc/init.d/RaspberInoServer stop";
char* init_script_file_start = "/etc/init.d/RaspberInoServer start";
char* init_script_file_status = "/etc/init.d/RaspberInoServer status";
char* raspberino_server = "/usr/local/bin/RaspberInoServer.py";
char* raspberino_server_path = "/usr/local/bin/";
char* raspberino_server_cmd = "python /usr/local/bin/RaspberInoServer.py";

char* raspberino_config_dir = "/etc/RaspberIno";
char* raspberino_config_file = "/etc/RaspberIno/config.cfg";
char* raspberino_cache_dir = "/etc/RaspberIno/data";

char* raspberino_log_file = "/var/log/RaspberInoServer.log";
char* raspberino_err_file = "/var/log/RaspberInoServer.err";

size_t write_data(void *ptr, size_t size, size_t nmemb, FILE *stream) {
    size_t written = fwrite(ptr, size, nmemb, stream);
    return written;
}

int FileExists(const char *filename)
{
 FILE *fp = fopen (filename, "r");
 if (fp!=NULL) fclose (fp);
 return (fp!=NULL);
}

int createInit(char* filename, char* user)
{
  FILE *init_template, *init_script;
  int temp = 1;
  int dir_line = 12;
  int cmd_line = 14;
  int usr_line = 16;
  int c;

  init_template = fopen(init_template_file, "r");
  init_script = fopen(init_script_file ,"w");

  c = getc(init_template);
  while(c != EOF)
  {
    if(c == '\n')
    {
      temp++;
    }
    if(temp == dir_line)
    {
      fputs("dir=\"", init_script);
      fputs(raspberino_server_path, init_script);
      fputs("\"\n", init_script);
      temp++;
    }
    else if(temp == cmd_line)
    {
      fputs("cmd=\"", init_script);
      fputs(raspberino_server_cmd, init_script);
      fputs("\"\n", init_script);
      temp++;
    }
    else if(temp == usr_line)
    {
      fputs("user=\"", init_script);
      fputs(user, init_script);
      fputs("\"\n", init_script);
      temp++;
    }
    else
    {
      putc(c, init_script);
    }
    c = getc(init_template);
  }
  int i = strtol("0755", 0, 8);
  chmod(init_script_file, i);
}

void startInstallation()
{
  char str[10];
  char user[40];
  char* config_file;

  echo();
  mvaddstr(2, 1, "Please configure before installation:");
  mvaddstr(3, 1, "Port: _____");
  mvaddstr(4, 1, "User: __________");
  mvgetnstr(3,7,str, 5);
  mvgetnstr(4,7,user, 5);
  if(!strcmp(str, ""))
    strcpy(str, "10000");
  if(!strcmp(user, ""))
    strcpy(user, "pi");
  mvwprintw(win, 1, 1, "Port: %s", str);
  mvwprintw(win, 1, 13, "User: %s", user);
  struct stat st = {0};
  if(stat("/usr/local/bin", &st) == -1)
  {
    mkdir("/usr/local/bin", 0700);
  }

  if(stat(raspberino_config_dir, &st) == -1)
  {
    mkdir(raspberino_config_dir, 0755);
    mvwaddstr(win, 3, 1, "Config folder created.");
  }
  else
  {
    mvwaddstr(win, 3, 1, "Config folder already exists.");
  }

  if(stat(raspberino_cache_dir, &st) == -1)
  {
    mkdir(raspberino_cache_dir, 0755);
    mvwaddstr(win, 4, 1, "Data folder created");
  }
  else
  {
    mvwaddstr(win, 4, 1, "Data folder already exists");
  }

  if(stat(raspberino_config_file, &st) == -1)
  {
    FILE *fp = fopen(raspberino_config_file, "ab+");
    fprintf(fp, "port=%s\n", str);
    int i = strtol("0755", 0, 8);
    chmod(raspberino_config_file, i);
    mvwaddstr(win, 5, 1, "Config file created.");
  }
  else
  {
    mvwaddstr(win, 5, 1, "Config file already exists.");
  }
  CURL *curl;
  FILE *fp;

  CURLcode res;
  char *url = "https://raw.githubusercontent.com/p4p4/RaspberinoServer/master/RaspberInoServer.py";
  curl = curl_easy_init();
  if(curl)
  {
    mvwaddstr(win, 6, 1, "Downloading server program.");
    fp = fopen(raspberino_server, "wb");
    curl_easy_setopt(curl, CURLOPT_URL, url);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_data);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, fp);
    res = curl_easy_perform(curl);
    curl_easy_cleanup(curl);
    fclose(fp);
  }
  char resolved_path[PATH_MAX];
  realpath(raspberino_server, resolved_path);
  mvwprintw(win, 6, 20, "File downloaded: %s", resolved_path);
  createInit("init_template", user);
  mvwaddstr(win, 7, 1, "Starting server...");
  system(init_script_file_start);
  mvwaddstr(win, 7, 20, "Done.");
  clear();
  delwin(menuwin);
  it = (ITEM**)calloc(4, sizeof(ITEM *));
  num_items = 3;
  it[0] = new_item("Update", "");
  it[1] = new_item("Uninstall", "");
  it[2] = new_item("Exit", "");
  menuwin = newwin(num_items, 15, y/4+y/2+1, 0);
  menu = new_menu(it);
  set_menu_win(menu, menuwin);
  post_menu(menu);
  menuquit = 0;
  refresh();
  wrefresh(menuwin);
  wrefresh(win);
}

void startUninstallation()
{
  mvwaddstr(win, 1, 1, "Stopping server");
  system(init_script_file_stop);
  mvwaddstr(win, 2, 1, "Deleting script");
  remove(raspberino_server);
  mvwaddstr(win, 3, 1, "Deleting init.d");
  remove(init_script_file);
  remove(raspberino_config_file);
  remove(raspberino_cache_dir);
  remove(raspberino_config_dir);
  remove(raspberino_log_file);
  remove(raspberino_err_file);
  mvwaddstr(win, 5, 1, "Done.");
  clear();
  delwin(menuwin);
  it = (ITEM**)calloc(4, sizeof(ITEM *));
  num_items = 2;
  it[0] = new_item("Install now", "");
  it[1] = new_item("Exit", "");
  menuwin = newwin(num_items, 20, y/4+y/2+1, 0);
  menu = new_menu(it);
  set_menu_win(menu, menuwin);
  post_menu(menu);
  menuquit = 0;
  refresh();
  wrefresh(menuwin);
  wrefresh(win);
}

void quitMenu(MENU *thismenu, ITEM **item, int items) {
  unpost_menu(thismenu);
  free_menu(thismenu);
  int i;
  for(i = 0; i < items; i++)
  {
    free_item(it[i]);
  }
  free(it);
  menuquit = 1;
}
void quit()
{
  if(menuquit == 0)
    quitMenu(menu, it, num_items);
  delwin(win);
  delwin(menuwin);
  endwin();
}

int main(void)
{
  initscr();
  clear();
  curs_set(0);
  noecho();
  cbreak();
  curs_set(0);
  atexit(quit);
  nl();
  keypad(stdscr, 1);

  if(FileExists(raspberino_server) == 1)
  {
    it = (ITEM**)calloc(4, sizeof(ITEM *));
    num_items = 3;
    it[0] = new_item("Update", "");
    it[1] = new_item("Uninstall", "");
    it[2] = new_item("Exit", "");
    menu = new_menu(it);
   }
  else
  {
    num_items = 2;
    it = (ITEM**)calloc(2, sizeof(ITEM *));
    it[0] = new_item("Install now", "");
    it[1] = new_item("Exit", "");
    menu = new_menu(it);
  }

  start_color();
  init_color(COLOR_WHITE, 500, 500, 500);
  init_pair(1,COLOR_WHITE, COLOR_BLUE);
  init_pair(2,COLOR_BLACK, COLOR_WHITE);

  int ch;
  getmaxyx(stdscr, y, x);

  win = newwin(y/2, x, y/4, 0);
  if(num_items == 2)
  {
    menuwin = newwin(num_items, 20, y/4+y/2+1, 0);
  }
  else
  {
    menuwin = newwin(num_items, 15, y/4+y/2+1, 0);
  }
bkgd(COLOR_PAIR(1));
  wbkgd(win, COLOR_PAIR(2));
  wbkgd(menuwin, COLOR_PAIR(2));

  set_menu_win(menu, menuwin);
  post_menu(menu);

  mvwaddstr(stdscr, 0, 1, "Welcome to RaspberIno installer!");
  mvwaddstr(win, 1, 1, "This program downloads the newest version of RaspberIno server");
  mvwaddstr(win, 2, 1, "and configures it.");
  mvwaddstr(win, 4, 1, "Installation can be cancelled by pressing 'q'");
  refresh();
  wrefresh(win);
  wrefresh(menuwin);
  while((ch = getch()) != 'q')
  {
    switch(ch)
    {
      case KEY_DOWN:
        menu_driver(menu, REQ_DOWN_ITEM);
        break;
      case KEY_UP:
        menu_driver(menu, REQ_UP_ITEM);
        break;
      case 0xA:
        if(((item_index(current_item(menu)) == 1 && num_items == 2) || (item_index(current_item(menu)) == 2 && num_items == 3)))
        {
          exit(0);
        }
        else if(item_index(current_item(menu)) == 0)
        {
          mvwaddstr(stdscr, 1, 1, "Installation started");
          wclear(win);
          quitMenu(menu, it, num_items);
          wclear(menuwin);
          startInstallation();
        }
        else if(item_index(current_item(menu)) == 1 && num_items == 3)
        {
          mvwaddstr(stdscr, 1, 1, "Uninstalling started");
          wclear(win);
          quitMenu(menu, it, num_items);
          wclear(menuwin);
          startUninstallation();
        }
    }
    wrefresh(menuwin);
    wrefresh(win);
    refresh();
  }
  return(0);
}
