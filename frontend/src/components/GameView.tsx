import React, { useEffect } from 'react';
import { Paper, IconButton, Typography, Box, Tooltip } from '@mui/material';
import ShareIcon from '@mui/icons-material/Share';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import GitHubIcon from '@mui/icons-material/GitHub';
import { Game } from '../types/game';

type Props = {
  game: Game;
  onBack: () => void;
};

export const GameView: React.FC<Props> = ({ game, onBack }) => {
  const [copied, setCopied] = React.useState(false);
  useEffect(() => {
    window.history.pushState({}, '', `/game/${game.project}`);
    return () => {
      window.history.pushState({}, '', '/');
    };
  }, [game.project]);

  return (
    <Paper sx={{ p: 2, position: 'relative', minHeight: '80vh' }}>
      <Box sx={{ position: 'absolute', top: 16, right: 16 }}>
        <IconButton
          onClick={() => window.open(`${process.env.REACT_APP_API_URL}/game/${game.project}`, '_blank')}
        >
          <OpenInNewIcon />
        </IconButton>
      </Box>
      <Box sx={{
        position: 'absolute',
        bottom: 16,
        left: 0,
        right: 0,
        display: 'flex',
        justifyContent: 'space-between',
        px: 2
      }}>
        <IconButton onClick={onBack}>
          <ArrowBackIcon />
        </IconButton>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title={copied ? "Link copied!" : "Copy link to clipboard"} open={copied}>
            <IconButton
              onClick={() => {
                navigator.clipboard.writeText(window.location.href);
                setCopied(true);
                setTimeout(() => {
                  setCopied(false);
                }, 2000);
              }}
            >
              <ShareIcon />
            </IconButton>
          </Tooltip>
          <IconButton
            onClick={() => window.open(`/game/${game.github_url}`, '_blank')}
            aria-label="View on GitHub"
          >
            <GitHubIcon />
          </IconButton>
        </Box>
      </Box>
      <Typography variant="h4" sx={{ mb: 2 }}>
        {game.project}
      </Typography>
      <iframe
        src={`${process.env.REACT_APP_API_URL}/game/${game.project}`}
        title={game.project}
        style={{ width: '100%', height: '70vh', border: 'none', backgroundColor: '#fff' }}
        sandbox="allow-same-origin allow-scripts allow-popups allow-forms allow-modals allow-pointer-lock"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
      />
    </Paper>
  );
}
