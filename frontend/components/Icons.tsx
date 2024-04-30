import { Info, LucideIcon, MoonStar, Sun, ThumbsUp, ThumbsDown, Copy, Plus, Send, Bot, User, Bookmark, BookmarkCheck, Hourglass } from 'lucide-react-native';
import { cssInterop } from 'nativewind';

function interopIcon(icon: LucideIcon) {
  cssInterop(icon, {
    className: {
      target: 'style',
      nativeStyleToProp: {
        color: true,
        opacity: true,
      },
    },
  });
}

interopIcon(Info);
interopIcon(MoonStar);
interopIcon(Sun);
interopIcon(ThumbsUp);
interopIcon(ThumbsDown);
interopIcon(Copy);
interopIcon(Plus);
interopIcon(Send);
interopIcon(Bot);
interopIcon(User);
interopIcon(Bookmark);
interopIcon(BookmarkCheck);
interopIcon(Hourglass);

export { Info, MoonStar, Sun, ThumbsUp, ThumbsDown, Copy, Plus, Send, Bot, User, Bookmark, BookmarkCheck, Hourglass };
