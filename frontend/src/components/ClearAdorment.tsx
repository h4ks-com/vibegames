import ClearIcon from '@mui/icons-material/Clear';
import { IconButton, InputAdornment } from '@mui/material';

type Props = {
  onClick: () => void;
};

export const ClearAdorment: React.FC<Props> = ({ onClick }) => (
  <InputAdornment position="end">
    <IconButton
      onClick={onClick}
      edge="end"
      aria-label="clear input"
      tabIndex={-1}
      sx={{ color: 'text.secondary' }}
    >
      <ClearIcon />
    </IconButton>
  </InputAdornment>
)
