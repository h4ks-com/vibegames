import React from 'react';
import { Paper, Typography, IconButton, Link, Box, Stack } from '@mui/material';
import PinDropIcon from '@mui/icons-material/PinDrop';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import CreateIcon from '@mui/icons-material/Create';
import VisibilityIcon from '@mui/icons-material/Visibility';
import GitHubIcon from '@mui/icons-material/GitHub';
import Tooltip from '@mui/material/Tooltip';
import { Game } from '../types/game';
import { GameThumbnail } from './GameThumbnail';

type Props = {
  game: Game;
  onGameClick: (game: Game) => void;
  onFavorite: (game: Game) => void;
  isFavorite: boolean;
  ref?: React.Ref<HTMLDivElement>;
};

export const GameCard: React.FC<Props> = ({ game, onGameClick, onFavorite, isFavorite, ref }) => {
  const handleGameClick = () => { onGameClick(game) };
  const handleFavoriteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onFavorite(game);
  };
  return (
    <Paper sx={{ p: 2, position: 'relative' }} ref={ref}>
      <Box sx={{ position: 'absolute', top: 8, right: 8, display: 'flex', gap: 1 }}>
        <IconButton
          size="small"
          sx={{ color: isFavorite ? 'orange' : 'inherit' }}
          onClick={handleFavoriteClick}
        >
          <PinDropIcon />
        </IconButton>
        <IconButton
          size="small"
          onClick={() => window.open(game.subdomain_url || game.path_url, '_blank')}
        >
          <OpenInNewIcon />
        </IconButton>
      </Box>

      <Typography variant="h6" sx={{ mb: 1, pr: 8 }}>{game.project}</Typography>

      <div onClick={handleGameClick} style={{ cursor: 'pointer' }}>
        <GameThumbnail
          thumbUrl={game.thumb_url}
          key={game.project}
        />
      </div>

      <Stack spacing={1} sx={{ mt: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <VisibilityIcon fontSize="small" />
          <Typography variant="body2">{game.num_opens}</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CreateIcon fontSize="small" />
          <Typography variant="body2">{new Date(game.date_added).toLocaleDateString()}</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AccessTimeIcon fontSize="small" />
          <Typography variant="body2">{new Date(game.date_modified).toLocaleDateString()}</Typography>
        </Box>
      </Stack>
      <Tooltip title="View on GitHub">
        <IconButton
          size="small"
          sx={{
            position: 'absolute',
            bottom: 8,
            right: 8,
            cursor: 'pointer',
          }}
          onClick={() => window.open(game.github_url, '_blank')}
        >
          <GitHubIcon />
        </IconButton>
      </Tooltip>
    </Paper>
  );
};
